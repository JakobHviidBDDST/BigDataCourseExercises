from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import uuid4
import json
import random
from hdfs.ext.avro import AvroWriter, AvroReader
from src.client import InsecureClient, get_hdfs_client
import threading


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

    def to_dict(self):
        self.created_at = self.created_at.timestamp()
        self.payload = json.dumps(self.payload.to_dict())
        return asdict(self)


VALID_SENSOR_IDS: list[int] = [1, 2, 3, 4, 5, 6]
VALID_TEMPORAL_ASPECTS: list[str] = ["real_time", "edge_prediction"]
VALID_RANGE: tuple[int] = (-600, 600)

SCHEMA = {
    "type": "record",
    "namespace": "default",
    "name": "SENSORPACKAGES",
    "fields": [
        {
            "name": "payload",
            "doc": "Payload of the message.",
            "type": "string"
        },
        {
            "name": "correlation_id",
            "doc": "UUID of this message.",
            "type": "string"
        },
        {
            "name": "created_at",
            "doc": "Timestamp (UTC) for msg creation.",
            "type": "double"
        },
        {
            "name": "schema_version",
            "doc": "Integer verion number of the msg schema.",
            "type": "int"
        },
    ]
}


def get_sensor_sample(sensor_id: int = None, modality: int = None, unit: str = "MW",
                      temporal_aspect: str = VALID_TEMPORAL_ASPECTS[0]) -> SensorObj:
    if sensor_id is None:
        sensor_id = random.choice(VALID_SENSOR_IDS)
    if modality is None:
        modality = random.choice(range(VALID_RANGE[0], VALID_RANGE[1] + 1))
    return SensorObj(sensor_id=sensor_id, modality=modality, unit=unit, temporal_aspect=temporal_aspect)


def get_filename(self, format: str = "avro") -> str:
    return f"/data/raw/sensor_id={self.payload.sensor_id}/temporal_aspect={self.payload.temporal_aspect}/{self.created_at.strftime('year=%Y/month=%m/day=%d')}/{self.correlation_id}.{format}"


def generate_sample(sensor_id: str, hdfs_client: InsecureClient) -> None:
    po = PackageObj(payload=get_sensor_sample(sensor_id=sensor_id))
    filename: str = get_filename(po)
    print("Filename: ", filename)
    with AvroWriter(client=hdfs_client, hdfs_path=filename, schema=SCHEMA, overwrite=True) as writer:
        writer.write(po.to_dict())
    with AvroReader(hdfs_client, filename) as reader:
        schema = reader.schema
        content = reader.content
        print("Sensor data: ", list(reader))
        print("\n")


class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def main():
    hdfs_client = get_hdfs_client()

    timer1 = RepeatTimer(1.0, generate_sample, [1, hdfs_client])
    timer2 = RepeatTimer(1.0, generate_sample, [2, hdfs_client])
    timer3 = RepeatTimer(1.0, generate_sample, [3, hdfs_client])
    timer4 = RepeatTimer(1.0, generate_sample, [4, hdfs_client])
    timer5 = RepeatTimer(1.0, generate_sample, [5, hdfs_client])
    timer6 = RepeatTimer(1.0, generate_sample, [6, hdfs_client])

    try:
        timer1.start()
        timer2.start()
        timer3.start()
        timer4.start()
        timer5.start()
        timer6.start()
        while True:
            pass

    except KeyboardInterrupt:
        pass
    finally:
        timer1.cancel()
        timer2.cancel()
        timer3.cancel()
        timer4.cancel()
        timer5.cancel()
        timer6.cancel()


if __name__ == "__main__":
    main()
