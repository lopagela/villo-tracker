import base64
import datetime
import pprint
import zlib
import json

if __name__ == '__main__':
    print("This script is used to parse the `Takn` (cpr_access_token -- an Oauth2 like token -- a JWT).\n"
          "The Takn is used for API access to JCDecaux bike system.\n"
          "It is not a secret, but it is not meant to be shared publicly.\n"
          "You can find it in your local storage in your browser. It is hardcored in the JavaScript code.\n\n"
          "To programmatically get this token, you can use the `component/commercial_bike.py` script.\n")
    input_token = input("Enter the token cpr_access_token, a.k.a. takn: ")

    # We don't care about the signature part of the JWT, so we can ignore it.
    jwt_header, jwt_payload, _ = input_token.split('.')

    # Decode the JWT header and verify its expected format.
    header = json.loads(base64.urlsafe_b64decode(jwt_header + '=='))
    print("Decoded JWT header:")
    pprint.pprint(header)
    if header.get('zip') != 'DEF':
        raise ValueError("Invalid JWT header format. Expected 'zip' to be 'DEF'")

    # Decode the JWT payload and verify its expected format.
    payload = json.loads(
        # Decompress the payload using zlib, which is expected to be compressed (c.f. `DEF` in the header).
        zlib.decompress(
            # Decode the urlsafe base64 encoded payload
            base64.urlsafe_b64decode(
                # Add padding to the base64 string to make it a valid base64 input.
                jwt_payload + '=='
            )
        )
    )

    print("Decoded JWT payload:")
    pprint.pprint(payload)

    print("The token is expiring at: ", datetime.datetime.fromtimestamp(payload['exp']))
