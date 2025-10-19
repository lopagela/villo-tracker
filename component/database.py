import logging
import os
import sqlite3
import pathlib
from typing import Any

log = logging.getLogger(__name__)

# See https://www.sqlite.org/changes.html
log.debug("Using underlying sqlite3 version=%s", sqlite3.sqlite_version)

OUTPUT_PATH = pathlib.Path("~/output/").expanduser()

if sqlite3.sqlite_version_info < (3, 35):
    # RETURNING in SQL syntax of SQLite require sqlite3>=3.35.0
    raise RuntimeError("sqlite3 version must be >=3.35.0")


class Database:
    def __init__(self, file_name: str | None = None) -> None:
        self.file_name = file_name or "commercial_bike.db"
        if self.get_db_path().exists():
            log.info("Database already exists")
        else:
            log.info("Creating database at path=%s", self.get_db_path())
            self._create_tables()
        self.connection = self.get_connection()
        self.cursor = self.connection.cursor()

    def get_db_path(self) -> pathlib.Path:
        return (OUTPUT_PATH / self.file_name).resolve()

    def get_connection(self):
        resolved_path = self.get_db_path()
        os.makedirs(resolved_path.parent, exist_ok=True)
        log.debug("Connecting to database at path=%s", resolved_path)
        connection = sqlite3.connect(resolved_path)
        connection.row_factory = sqlite3.Row  # Results will be returned as dictionaries (ish)
        return connection

    def _create_tables(self):
        connection = self.get_connection()
        connection.execute("""
                           CREATE TABLE stations
                           (
                               -- id                   INTEGER PRIMARY KEY AUTOINCREMENT -- we are using `rowid` from SQLite instead
                               number               INTEGER NOT NULL UNIQUE, -- the API id of this station
                               name                 TEXT,                    -- A short name representing the name of the station
                               address              TEXT,                    -- some textual representation of the address of the bike station
                               latitude             REAL,                    -- GPS latitude
                               longitude            REAL,                    -- GPS longitude
                               total_stand_capacity INTEGER                  -- the total number of bike slots at this station
                           )
                           """)
        connection.execute("""
                           CREATE TABLE bikes_evolution
                           (
                               -- id         INTEGER PRIMARY KEY AUTOINCREMENT,           -- internal id of this bike delta -- we are using `rowid` from SQLite instead
                               at         TIMESTAMP NOT NULL,
                               station_id INTEGER   NOT NULL REFERENCES stations (rowid), -- the internal id of the station (NOT THE API number of this station) -- i.e. the stations.rowid value !!!
                               bike_id    TEXT      NOT NULL,                          -- the UUID of the affected bike
                               action     TEXT      NOT NULL                           -- I or O (I for IN, and O for OUT): what this bike did at this statio
                           )
                           """)
        # TODO maybe create an index on bikes_evolution.station_id to make retrieval faster??

        connection.commit()
        connection.close()

    def save_stations(self, stations: list[dict[str, Any]]) -> None:
        # RETURNING require sqlite3>=3.35.0
        # https://stackoverflow.com/a/60045014
        self.cursor.executemany(
            """
            INSERT INTO stations (number, name, address, latitude, longitude, total_stand_capacity)
            VALUES (:number, :name, :address, :latitude, :longitude, :total_stand_capacity)
            """, stations)
        self.connection.commit()

    def find_all_stations(self) -> list[dict[str, Any]]:
        return self.cursor.execute(
            """
            SELECT rowid, number, name, address, latitude, longitude, total_stand_capacity
            FROM stations
            """
        ).fetchall()

    def find_all_bikes_evolutions_by_station_id(self, station_id: int) -> list[dict[str, Any]]:
        """Return all bikes evolutions by station id, as a list of dicts (more like a list of sqlite3.Row)"""
        return self.cursor.execute(
            """SELECT at, station_id, bike_id, action
               FROM bikes_evolution
               WHERE station_id = :station_id
            """, (station_id,)
        ).fetchall()

    def save_bikes_evolutions(self, bike_evolutions: list[dict[str, Any]]) -> None:
        self.cursor.executemany(
            """
            INSERT INTO bikes_evolution (at, station_id, bike_id, action)
            VALUES (:at, :station_id, :bike_id, :action)
            """, bike_evolutions)
        self.connection.commit()
