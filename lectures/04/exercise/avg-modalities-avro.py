from pyspark.sql import functions as F
from pyspark.sql import types as T
from src.utils import FS, SPARK_ENV, get_spark_context


def get_avro_files(base_path: str = FS) -> str:
    return f"{base_path}/data/raw/sensor_id=*/temporal_aspect=*/year=*/month=*/day=*/*.avro"


if __name__ == "__main__":
    additional_conf = {
        "spark.jars.packages": "org.apache.spark:spark-avro_2.12:3.5.2"
    }

    spark = get_spark_context(
        app_name="Sample Sum Avro",
        config=SPARK_ENV.K8S,
        additional_conf=additional_conf
    )

    df = spark.read.format("avro").load(get_avro_files())

    # Display schema to understand the data structure
    df.printSchema()

    payload_schema = T.StructType([
        T.StructField("sensor_id", T.StringType(), False),
        T.StructField("modality", T.FloatType(), False),
        T.StructField("unit", T.StringType(), False),
        T.StructField("temporal_aspect", T.StringType(), False),
    ])

    df = df.withColumn("json_payload", F.from_json(F.col("payload"), payload_schema))
    df = df.select("correlation_id", "created_at", "schema_version", "json_payload.*")

    # Display the schema after parsing the payload
    df.printSchema()
    df.show()

    # Group by sensor_id and calculate the average modality
    df_gr = df.groupBy("sensor_id").agg(
        F.avg("modality").alias("avg_modality")
    )

    # Show the result
    df_gr.show()

    # Stop the Spark session
    spark.stop()
