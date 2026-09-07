import datetime
import random

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base

N_EXPERIMENTS: int = 25
N_SAMPLES: int = 1000

Base = declarative_base()


class Experiment(Base):
    __tablename__ = "experiment"
    id = Column(Integer, primary_key=True, nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"Experiment(id={self.id}, created_date={self.created_date})"


class Results(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiment.id"), nullable=False)
    value = Column(Double, nullable=False)
    valid = Column(Boolean, nullable=False)

    def __repr__(self) -> str:
        return f"Results(id={self.id}, experiment_id={self.experiment_id}, value={self.value}, valid={self.valid})"


# insert view manual
# CREATE VIEW analysis AS SELECT r.experiment_id, e.created_date, r.valid, AVG(r.value) avg_value FROM results r INNER JOIN experiment e ON r.experiment_id=e.id GROUP BY r.experiment_id, r.valid;


def create_new_expirment() -> Column[int]:
    with Session(engine) as session:
        ex = Experiment()
        session.add(ex)
        session.commit()
        session.refresh(ex)

    return ex.id


def create_results(experiment_id: Column[int], n: int):
    with Session(engine) as session:
        session.add_all(
            [
                Results(
                    experiment_id=experiment_id,
                    value=random.random(),
                    valid=random.choice([True, False]),
                )
                for _ in range(n)
            ]
        )
        session.commit()


if __name__ == "__main__":
    # create SQL engine
    print(f"Establish connection...")
    engine = create_engine("mysql+pymysql://root:datahubdatahub@127.0.0.1:3306/datahub")

    print(f"Creating tables if needed...")
    #
    Base.metadata.create_all(engine)

    # log expirments
    for i in range(N_EXPERIMENTS):
        print(f"Experiment {i+1} of {N_EXPERIMENTS}...", end="\r")
        ex_id = create_new_expirment()
        create_results(ex_id, N_SAMPLES)
    print(f"\nDone...")
