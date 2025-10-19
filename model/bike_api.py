"""
Old DTOs and some other nice data accessor.
Written by Le Chat, from Mistral AI.
"""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Rating:
    count: int | None = None
    lastRatingDateTime: str | None = None
    value: float | None = None

@dataclass
class Battery:
    level: int | None = None
    percentage: int | None = None
    type: str | None = None

@dataclass
class Bike:
    bikeBatteryMv: int | None = None
    checked: bool | None = None
    contractName: str | None = None
    createdAt: str | None = None
    energySource: int | None = None
    frameId: str | None = None
    hasBattery: bool | None = None
    hasLock: bool | None = None
    id: str | None = None
    isReserved: bool | None = None
    number: int | None = None
    standNumber: int | None = None
    stationNumber: int | None = None
    status: str | None = None
    statusLabel: str | None = None
    type: str | None = None
    updatedAt: str | None = None
    lastDataFrameDate: str | None = None
    bikeTopHwVersion: str | None = None
    bikeTopSwVersion: str | None = None
    bmsSwVersion: str | None = None
    motorControllerHwVersion: str | None = None
    motorControllerSwVersion: str | None = None
    zedSwVersion: str | None = None
    rating: Rating = field(default_factory=Rating)
    battery: Battery = field(default_factory=Battery)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Bike':
        rating_data = data.get('rating', {})
        battery_data = data.get('battery', {})

        return cls(
            bikeBatteryMv=data.get('bikeBatteryMv'),
            checked=data.get('checked'),
            contractName=data.get('contractName'),
            createdAt=data.get('createdAt'),
            energySource=data.get('energySource'),
            frameId=data.get('frameId'),
            hasBattery=data.get('hasBattery'),
            hasLock=data.get('hasLock'),
            id=data.get('id'),
            isReserved=data.get('isReserved'),
            number=data.get('number'),
            standNumber=data.get('standNumber'),
            stationNumber=data.get('stationNumber'),
            status=data.get('status'),
            statusLabel=data.get('statusLabel'),
            type=data.get('type'),
            updatedAt=data.get('updatedAt'),
            lastDataFrameDate=data.get('lastDataFrameDate'),
            bikeTopHwVersion=data.get('bikeTopHwVersion'),
            bikeTopSwVersion=data.get('bikeTopSwVersion'),
            bmsSwVersion=data.get('bmsSwVersion'),
            motorControllerHwVersion=data.get('motorControllerHwVersion'),
            motorControllerSwVersion=data.get('motorControllerSwVersion'),
            zedSwVersion=data.get('zedSwVersion'),
            rating=Rating(
                count=rating_data.get('count'),
                lastRatingDateTime=rating_data.get('lastRatingDateTime'),
                value=rating_data.get('value')
            ),
            battery=Battery(
                level=battery_data.get('level'),
                percentage=battery_data.get('percentage'),
                type=battery_data.get('type')
            )
        )

class BikeCSVSerializer:
    @staticmethod
    def get_header() -> list[str]:
        return [
            'id',
            'frameId',
            'number',
            'standNumber',
            'rating_count',
            'rating_lastRatingDateTime',
            'rating_value',
            'bikeBatteryMv',
            'checked',
            'contractName',
            'createdAt',
            'updatedAt',
            'energySource',
            'hasBattery',
            'hasLock',
            'isReserved',
            'stationNumber',
            'status',
            'statusLabel',
            'type',
            'battery_level',
            'battery_percentage',
            'battery_type',
            'bikeTopHwVersion',
            'bikeTopSwVersion',
            'bmsSwVersion',
            'lastDataFrameDate',
            'motorControllerHwVersion',
            'motorControllerSwVersion',
            'zedSwVersion'
        ]

    @staticmethod
    def get_row(bike: Bike) -> list:
        return [
            bike.id,
            bike.frameId,
            bike.number,
            bike.standNumber,
            bike.rating.count,
            bike.rating.lastRatingDateTime,
            bike.rating.value,
            bike.bikeBatteryMv,
            bike.checked,
            bike.contractName,
            bike.createdAt,
            bike.updatedAt,
            bike.energySource,
            bike.hasBattery,
            bike.hasLock,
            bike.isReserved,
            bike.stationNumber,
            bike.status,
            bike.statusLabel,
            bike.type,
            bike.battery.level,
            bike.battery.percentage,
            bike.battery.type,
            bike.bikeTopHwVersion,
            bike.bikeTopSwVersion,
            bike.bmsSwVersion,
            bike.lastDataFrameDate,
            bike.motorControllerHwVersion,
            bike.motorControllerSwVersion,
            bike.zedSwVersion
        ]

