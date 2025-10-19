
import csv
import json
import logging
import time
from pathlib import Path
from datetime import datetime as dt

from component.commercial_bike import CommercialBikeClient
from component.database import Database
from model.bike_api import Bike, BikeCSVSerializer
from model.station_api import Station, StationCSVSerializer

log = logging.getLogger(__name__)

class VilloTrackerApp:
    BRUSSELS_WEBSITE = "https://www.villo.be"
    LYON_WEBSITE = "https://velov.grandlyon.com"

    def __init__(self):

        # TODO use a rondom user agent at every requests, to try and blur our marks on their webservers (to prevent fail2ban / blocking)
        self.api_client = CommercialBikeClient(self.BRUSSELS_WEBSITE)
        self.db = Database()

    def _init_stations_db(self):
        stations = [Station.from_dict(station) for station in self.api_client.get_stations()]
        stations_to_save = [{
            "number": st.number,
            "name": st.name,
            "address": st.address,
            "latitude": st.position.latitude,
            "longitude": st.position.longitude,
            "total_stand_capacity": st.totalStands.capacity,
        }
            for st in stations
        ]
        self.db.save_stations(stations=list(stations_to_save))

    def _init_bikes_evolution_db(self):
        for station in self.db.find_all_stations():
            log.info("Scanning station %s", station["number"])
            api_station_id = station["number"]
            internal_station_id = station["rowid"]  # SQLite rowid -- the primary key in SQLite of our table
            bikes = [Bike.from_dict(bike) for bike in self.api_client.get_bikes_at_station(station_id=api_station_id)]
            log.debug("Found count=%d bikes at station=%s", len(bikes), api_station_id)
            # Considering all the bikes as IN for initialization
            now = dt.now()
            bikes_evolutions = [{
                "at": now,
                "station_id": internal_station_id,
                "bike_id": bi.id,
                "action": "I",  # I for IN, O for OUT
            } for bi in bikes]
            self.db.save_bikes_evolutions(list(bikes_evolutions))
            log.debug("Sleeping a bit to prevent being blocked")
            time.sleep(1)

    def _debug_one_shot_csv(self):
        raw_stations = self.api_client.get_stations()
        Path("~/output/raw_json/stations.json").expanduser().write_text(json.dumps(raw_stations, indent=2))
        stations = [Station.from_dict(station) for station in raw_stations]
        with Path("~/output/csv/stations.csv").expanduser().open(mode="w") as stations_file:
            stations_writer = csv.writer(stations_file, dialect=csv.unix_dialect, quoting=csv.QUOTE_ALL)
            # headers writing
            stations_writer.writerow(StationCSVSerializer.get_header())

            for station in stations:
                stations_writer.writerow(StationCSVSerializer.get_row(station))

        station_num = "34"
        raw_bikes = self.api_client.get_bikes_at_station(station_num)
        Path(f"~/output/raw_json/bikes_at_{station_num}.json").expanduser().write_text(json.dumps(raw_bikes, indent=2))
        bikes_at_station = [Bike.from_dict(bike) for bike in raw_bikes]
        with Path(f"~/output/csv/bikes_at_{station_num}.csv").expanduser().open(mode="w") as stations_file:
            bike_writer = csv.writer(stations_file, dialect=csv.unix_dialect, quoting=csv.QUOTE_ALL)
            # headers writing
            bike_writer.writerow(BikeCSVSerializer.get_header())

            for bike in bikes_at_station:
                bike_writer.writerow(BikeCSVSerializer.get_row(bike))


if __name__ == "__main__":
    app = VilloTrackerApp()
    app._init_stations_db()
    app._init_bikes_evolution_db()
    app._debug_one_shot_csv()

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
