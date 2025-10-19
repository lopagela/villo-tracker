from dataclasses import dataclass, field
from typing import Any

@dataclass
class Position:
    latitude: float | None = None
    longitude: float | None = None

@dataclass
class Availabilities:
    bikes: int | None = None
    electricalBikes: int | None = None
    electricalInternalBatteryBikes: int | None = None
    electricalRemovableBatteryBikes: int | None = None
    mechanicalBikes: int | None = None
    stands: int | None = None

@dataclass
class Stands:
    availabilities: Availabilities = field(default_factory=Availabilities)
    capacity: int | None = None

@dataclass
class Station:
    address: str | None = None
    banking: bool | None = None
    bonus: bool | None = None
    connected: bool | None = None
    contractName: str | None = None
    lastUpdate: str | None = None
    name: str | None = None
    number: int | None = None
    overflow: bool | None = None
    overflowStands: Any | None = None
    shape: Any | None = None
    status: str | None = None
    position: Position = field(default_factory=Position)
    mainStands: Stands = field(default_factory=Stands)
    totalStands: Stands = field(default_factory=Stands)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Station':
        position_data = data.get('position', {})
        main_stands_data = data.get('mainStands', {})
        total_stands_data = data.get('totalStands', {})

        return cls(
            address=data.get('address'),
            banking=data.get('banking'),
            bonus=data.get('bonus'),
            connected=data.get('connected'),
            contractName=data.get('contractName'),
            lastUpdate=data.get('lastUpdate'),
            name=data.get('name'),
            number=data.get('number'),
            overflow=data.get('overflow'),
            overflowStands=data.get('overflowStands'),
            shape=data.get('shape'),
            status=data.get('status'),
            position=Position(
                latitude=position_data.get('latitude'),
                longitude=position_data.get('longitude')
            ),
            mainStands=Stands(
                availabilities=Availabilities(
                    bikes=main_stands_data.get('availabilities', {}).get('bikes'),
                    electricalBikes=main_stands_data.get('availabilities', {}).get('electricalBikes'),
                    electricalInternalBatteryBikes=main_stands_data.get('availabilities', {}).get('electricalInternalBatteryBikes'),
                    electricalRemovableBatteryBikes=main_stands_data.get('availabilities', {}).get('electricalRemovableBatteryBikes'),
                    mechanicalBikes=main_stands_data.get('availabilities', {}).get('mechanicalBikes'),
                    stands=main_stands_data.get('availabilities', {}).get('stands')
                ),
                capacity=main_stands_data.get('capacity')
            ),
            totalStands=Stands(
                availabilities=Availabilities(
                    bikes=total_stands_data.get('availabilities', {}).get('bikes'),
                    electricalBikes=total_stands_data.get('availabilities', {}).get('electricalBikes'),
                    electricalInternalBatteryBikes=total_stands_data.get('availabilities', {}).get('electricalInternalBatteryBikes'),
                    electricalRemovableBatteryBikes=total_stands_data.get('availabilities', {}).get('electricalRemovableBatteryBikes'),
                    mechanicalBikes=total_stands_data.get('availabilities', {}).get('mechanicalBikes'),
                    stands=total_stands_data.get('availabilities', {}).get('stands')
                ),
                capacity=total_stands_data.get('capacity')
            )
        )

class StationCSVSerializer:
    @staticmethod
    def get_header() -> list[str]:
        return [
            'number',
            'name',
            'address',
            'lastUpdate',
            'position_latitude',
            'position_longitude',
            'banking',
            'bonus',
            'connected',
            'contractName',
            'overflow',
            'status',
            'mainStands_availabilities_bikes',
            'mainStands_availabilities_electricalBikes',
            'mainStands_availabilities_electricalInternalBatteryBikes',
            'mainStands_availabilities_electricalRemovableBatteryBikes',
            'mainStands_availabilities_mechanicalBikes',
            'mainStands_availabilities_stands',
            'mainStands_capacity',
            'totalStands_availabilities_bikes',
            'totalStands_availabilities_electricalBikes',
            'totalStands_availabilities_electricalInternalBatteryBikes',
            'totalStands_availabilities_electricalRemovableBatteryBikes',
            'totalStands_availabilities_mechanicalBikes',
            'totalStands_availabilities_stands',
            'totalStands_capacity'
        ]

    @staticmethod
    def get_row(station: Station) -> list:
        return [
            station.number,
            station.name,
            station.address,
            station.lastUpdate,
            station.position.latitude,
            station.position.longitude,
            station.banking,
            station.bonus,
            station.connected,
            station.contractName,
            station.overflow,
            station.status,
            station.mainStands.availabilities.bikes,
            station.mainStands.availabilities.electricalBikes,
            station.mainStands.availabilities.electricalInternalBatteryBikes,
            station.mainStands.availabilities.electricalRemovableBatteryBikes,
            station.mainStands.availabilities.mechanicalBikes,
            station.mainStands.availabilities.stands,
            station.mainStands.capacity,
            station.totalStands.availabilities.bikes,
            station.totalStands.availabilities.electricalBikes,
            station.totalStands.availabilities.electricalInternalBatteryBikes,
            station.totalStands.availabilities.electricalRemovableBatteryBikes,
            station.totalStands.availabilities.mechanicalBikes,
            station.totalStands.availabilities.stands,
            station.totalStands.capacity
        ]
