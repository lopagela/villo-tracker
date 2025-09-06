import base64
import datetime
import json
import logging
import pprint
import urllib.request, urllib.parse
import re
import zlib
from functools import lru_cache

COMPACT_LOG_FORMAT = '%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s - %(message)s'
logging.basicConfig(level="DEBUG", format=COMPACT_LOG_FORMAT, datefmt="%H:%M:%S")
logging.captureWarnings(True)
log = logging.getLogger(__name__)

# Typically, we find `<link rel="modulepreload" href="chunk-...">` in the HTML, at the end of the body.
# We are using these to find the JavaScript chunks that are loaded by the page.
# This approach is relatively weak, as it relies on this specific implementation.
# To have a strong implementation, we would need to more exhaustively parse the HTML and JavaScript.
CHUNK_PATH_RE = re.compile(r'href="(chunk-[^"]+\.js)"')

# Same here, this implementation is weak, as it relies on the specific structure of the JS code.
# A stronger implementation would be to execute the JavaScript code and extract the OAuth2 details from there.
OAUTH2_RE = re.compile(r',oAuth:{(.*?)}')
JS_OBJ_FIELDS_RE = re.compile(
    r'([a-zA-Z]+):"([^"]+?)"')  # Matches key-value pairs in the OAuth2 object (in the JS object), e.g., `client_id:"abc123"`

CONTRACT_RE = re.compile(r',contract:{(.*?)}')
STATIONS_RE = re.compile(r'stations:{(.*?)}')


class OAuth2Token:
    def __init__(
            self,
            auth_host: str,
            access_token: str,
            refresh_token: str,
    ) -> None:
        self.auth_host = auth_host
        self.access_token = access_token
        self.refresh_token = refresh_token

    @classmethod
    @lru_cache(maxsize=1)  # Cache size of 1, as we only need one value at a time.
    def access_token_expires_at(cls, access_token: str) -> datetime.datetime:
        jwt_header, jwt_payload, _ = access_token.split('.')

        # Decode the JWT payload and verify its expected format.
        payload = json.loads(
            zlib.decompress(
                base64.urlsafe_b64decode(jwt_payload + '==')
            )
        )
        return datetime.datetime.fromtimestamp(int(payload['exp']), tz=datetime.timezone.utc)

    @property
    def expires_at(self) -> datetime.datetime:
        return self.access_token_expires_at(self.access_token)

    def __repr__(self):
        return f"OAuth2Token(access_token={self.access_token}, refresh_token={self.refresh_token}, expires_at={self.expires_at})"


def search_config_in_js(
        js_content: str,
        re_pattern_name: re.Pattern = OAUTH2_RE,
        re_pattern_content: re.Pattern = JS_OBJ_FIELDS_RE,
) -> None | dict[str, str]:
    """
    Searches for a specific key in the JavaScript content and returns its value.
    The key is expected to be in the format `key: "value"`.
    """
    match = re_pattern_name.search(js_content)
    if not match:
        # No match found, return None
        return None
    content_js_obj_matched = match.group(1)
    log.debug(f"Found a match for regex=%s for the JS object name: %s", re_pattern_name, content_js_obj_matched)
    if not content_js_obj_matched:
        raise RuntimeError("No OAuth2 details found in any of the JavaScript chunks. You have "
                           "to update the detection logic in this script to match the current website structure.")

    js_variables: dict[str, str] = {
        key: value for key, value in re_pattern_content.findall(content_js_obj_matched)
    }
    log.debug(f"Extracted JS variables: %s", js_variables)
    return js_variables


class CommercialBikeAuthComponent:
    def __init__(self, baseurl: str):
        self.baseurl = baseurl

        self.api_contract_info: dict[str, str] = {}
        self.api_stations_info: dict[str, str] = {}

    def _get_website_content_at_path(self, path: str) -> str:
        url = urllib.parse.urljoin(self.baseurl, path)
        log.debug(f"Downloading url=%s", url)
        try:
            with urllib.request.urlopen(url) as response:
                byte_content = response.read()
            log.debug(f"Downloaded count=%s bytes from url=%s", len(byte_content), url)
            return byte_content.decode('utf-8')
        except Exception as e:
            raise RuntimeError(f"Failed to download {url}: {e}")

    def _get_oauth2_details(self) -> dict[str, str]:
        content = self._get_website_content_at_path("/fr/mapping")
        log.debug("Content downloaded successfully")
        # Looking to find all the JS chunks present in the page
        chunks = CHUNK_PATH_RE.findall(content)
        if not chunks:
            raise RuntimeError("No JavaScript chunks found in the page content.")
        log.debug(f"Found {len(chunks)} JavaScript chunks: {chunks}")

        oauth2_details, chunk_content = {}, None
        while chunks:
            chunk = chunks.pop()
            log.debug(f"Processing chunk=%s", chunk)
            chunk_content = self._get_website_content_at_path(chunk)
            oauth2_details = search_config_in_js(
                chunk_content,
                re_pattern_name=OAUTH2_RE,
                re_pattern_content=JS_OBJ_FIELDS_RE
            )
            if not oauth2_details:
                log.info(f"No OAuth2 details found in chunk=%s. Continuing to the next chunk.", chunk)
                continue

            if not {"authHost", "env", "clientCode", "clientKey"}.issubset(oauth2_details.keys()):
                log.info("Incomplete OAuth2 details found in the raw JavaScript object. Continuing to search in the next chunk.")
                oauth2_details = {}  # Invalid details, so we delete the dict to avoid confusion.
                continue
            # If we reach here, we have found the OAuth2 details in one of the chunks.
            break

        if not oauth2_details:
            raise RuntimeError("No OAuth2 details found in the raw JavaScript object. "
                               "You have to update the detection logic in this script to match the current website structure.")
        log.info(f"Extracted OAuth2 details: {oauth2_details}")

        # We also extract the contract details from the same JS object.
        # WARNING: THIS IS EXTREMELY WEAK, as it relies on the specific structure of the JS code.
        self.api_contract_info = search_config_in_js(
            chunk_content,  # Latest chunk content
            re_pattern_name=CONTRACT_RE,
            re_pattern_content=JS_OBJ_FIELDS_RE
        )
        self.api_stations_info = search_config_in_js(
            chunk_content,  # Latest chunk content
            re_pattern_name=STATIONS_RE,
            re_pattern_content=JS_OBJ_FIELDS_RE
        )
        return oauth2_details

    def get_oauth2_tokens(self) -> OAuth2Token:
        oauth2_details = self._get_oauth2_details()
        # Do a POST request to the OAuth2 endpoint to get the client token (access token)

        url = oauth2_details["authHost"] + "/environments/" + oauth2_details["env"] + "/client_tokens"
        post_body = {
            "code": oauth2_details["clientCode"],
            "key": oauth2_details["clientKey"]
        }
        log.debug(f"POSTing to url=%s with body=%s", url, post_body)
        request = urllib.request.Request(
            url=url,
            data=json.dumps(post_body).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(request) as response:
            response_data = response.read()
        log.debug(f"Response received with body=%s", response_data)
        client_tokens = json.loads(response_data)
        log.info(f"Received the following client_tokens=%s", client_tokens)
        if not client_tokens:
            raise RuntimeError("No access token found in the response. You have to update the detection logic "
                               "in this script to match the current website structure.")
        return OAuth2Token(
            auth_host=oauth2_details["authHost"],
            access_token=client_tokens['accessToken'],
            refresh_token=client_tokens['refreshToken'],
        )

    @classmethod
    def refresh_oauth2_tokens(cls, oauth2_tokens: OAuth2Token) -> OAuth2Token:
        # Do a POST request to the OAuth2 endpoint to refresh the client token (access token)

        url = oauth2_tokens.auth_host + "/access_tokens"
        post_body = {
            "refreshToken": oauth2_tokens.refresh_token
        }
        log.debug(f"POSTing to url=%s with body=%s", url, post_body)
        request = urllib.request.Request(
            url=url,
            data=json.dumps(post_body).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(request) as response:
            response_data = response.read()
        log.debug(f"Response received with body=%s", response_data)
        client_tokens = json.loads(response_data)
        log.info(f"Received the following refreshed client_tokens=%s", client_tokens)
        if not client_tokens:
            raise RuntimeError("No access token found in the response. You have to update the detection logic "
                               "in this script to match the current website structure.")
        return OAuth2Token(
            auth_host=oauth2_tokens.auth_host,
            refresh_token=oauth2_tokens.refresh_token,
            # New access token
            access_token=client_tokens['accessToken'],
        )



class CommercialBikeClient:
    def __init__(self, baseurl: str):
        self.auth = CommercialBikeAuthComponent(baseurl)

        # Internal cache, not to be used directly.
        self._cached_oauth2_tokens = self.auth.get_oauth2_tokens()

    def api_authorization_header(self) -> str:
        """
        Returns the authorization header to be used in API requests.
        """
        if self._cached_oauth2_tokens.expires_at < datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=30):
            # Tokens are valid for around 2h
            log.info("Access token is expired or about to expire, refreshing it.")
            self._cached_oauth2_tokens = self.auth.refresh_oauth2_tokens(self._cached_oauth2_tokens)
        return f"Taknv1 {self._cached_oauth2_tokens.access_token}"

    def get_stations(self) -> dict[str, str]:
        """
        Returns the stations information from the API.
        """
        # Call to GET self.auth.api_station['url'] to get the stations information with QS `apiKey` and `contract` set
        url = self.auth.api_stations_info['url']
        params = {
            'apiKey': self.auth.api_stations_info['apiKey'],
            'contract': self.auth.api_contract_info['name']
        }
        log.debug(f"GETing url=%s with params=%s", url, params)
        request = urllib.request.Request(
            url=url + '?' + urllib.parse.urlencode(params),
            headers={'Authorization': self.api_authorization_header()}
        )
        with urllib.request.urlopen(request) as response:
            response_data = response.read()
        log.debug(f"Response received with body=%s", response_data)
        stations_info = json.loads(response_data)
        pprint.pprint(stations_info)
        return stations_info

    def get_bikes_at_station(self, station_id: str) -> dict[str, str]:
        """
        Returns the bikes information at a specific station.
        """
        # Call to GET self.auth.api_station['url'] with QS `apiKey` and `contract` set
        url = urllib.parse.urljoin(self._cached_oauth2_tokens.auth_host, f"/contracts/{self.auth.api_contract_info['name']}/bikes")
        params = {
            'stationNumber': station_id
        }
        log.debug(f"GETing url=%s with params=%s", url, params)
        request = urllib.request.Request(
            url=url + '?' + urllib.parse.urlencode(params),
            headers={
                'Authorization': self.api_authorization_header(),
                "Accept": "application/vnd.bikes.v4+json"
            }
        )
        with urllib.request.urlopen(request) as response:
            response_data = response.read()
        log.debug(f"Response received with body=%s", response_data)
        bikes_info = json.loads(response_data)
        pprint.pprint(bikes_info)
        return bikes_info



if __name__ == "__main__":
    BRUSSELS_WEBSITE = "https://www.villo.be"
    LYON_WEBSITE = "https://velov.grandlyon.com"

    # TODO fix me for Lyon
    api_client = CommercialBikeClient(BRUSSELS_WEBSITE)

    api_client.get_stations()
    api_client.get_bikes_at_station("34")

    # TODO
    #    * Create an SQLite DB
    #    * Create a table in DB to store the stations with the following attributes
    #      * address
    #      * connected
    #      * contractName
    #      * lastUpdate
    #      * name
    #      * number (make it id as well of this table -- used below)
    #      * position_latitude
    #      * position_longitude
    #      * status
    #      * totalStands_capacity
    #    * Create a table in DB to store all the bikes
    #      * id (UUID apparently)
    #      * frameId
    #      * CONTINUE TO SEARCH THE OTHER FIELDS of bikes !!!
    #    * Create a table in DB to store the changes in bikes at station
    #      * station_id (the id of the station above)
    #      * station_id (the id of the station above)
