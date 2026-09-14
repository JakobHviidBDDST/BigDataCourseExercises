from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import uuid4
import random
import json

VALID_SENSOR_IDS: list[int] = [1, 2, 3, 4, 5, 6]
VALID_TEMPORAL_ASPECTS: list[str] = ["real_time", "edge_prediction"]
VALID_RANGE: tuple[int] = (-600, 600)


def get_uuid():
    return str(uuid4())


@dataclass
class SensorObj:
    sensor_id: str
    modality: float
    unit: str
    temporal_aspect: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PackageObj:
    payload: SensorObj
    correlation_id: str = field(default_factory=get_uuid)
    created_at: datetime = field(default_factory=datetime.utcnow)
    schema_version: int = field(default=1)

    def __post_init__(self):
        self.payload = (
            self.str_to_sensor_obj(self.payload)
            if isinstance(self.payload, str)
            else self.payload
        )

    def str_to_sensor_obj(self, x: str) -> SensorObj:
        return SensorObj(**json.loads(x))

    def to_dict(self):
        self.created_at = self.created_at.timestamp()
        self.payload = json.dumps(self.payload.to_dict())
        return asdict(self)


def get_sensor_sample(
        sensor_id: int = None,
        modality: int = None,
        unit: str = "MW",
        temporal_aspect: str = VALID_TEMPORAL_ASPECTS[0],
) -> SensorObj:
    if sensor_id is None:
        sensor_id = random.choice(VALID_SENSOR_IDS)
    if modality is None:
        modality = random.choice(range(VALID_RANGE[0], VALID_RANGE[1] + 1))
    return SensorObj(
        sensor_id=sensor_id,
        modality=modality,
        unit=unit,
        temporal_aspect=temporal_aspect,
    )


def generate_sample(sensor_id: int) -> tuple[int, dict]:
    po = PackageObj(payload=get_sensor_sample(sensor_id=sensor_id))
    return sensor_id, po.to_dict()
