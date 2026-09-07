from pyspark.sql import functions as F
from pyspark.sql import types as T
from src.utils import FS, SPARK_ENV, get_spark_context

if __name__ == "__main__":
    spark = get_spark_context(app_name="Sample Sum", config=SPARK_ENV.K8S)
    sc = spark.sparkContext
    files = sc.wholeTextFiles(f"{FS}/topics/INGESTION/*/*.json")
    json_schema = T.StructType(
        [
            T.StructField("correlation_id", T.StringType(), False),
            T.StructField("created_at", T.StringType(), False),
            T.StructField("payload", T.StringType(), False),
            T.StructField("schema_version", T.LongType(), False),
        ]
    )

    payload_schema = T.StructType(
        [
            T.StructField("sensor_id", T.LongType(), False),
            T.StructField("modality", T.FloatType(), False),
            T.StructField("unit", T.StringType(), False),
            T.StructField("temporal_aspect", T.StringType(), False),
        ]
    )

    # parse the json files and create a dataframe with schema
    df = spark.read.json(files.values(), schema=json_schema)
    df = df.withColumn("payload", F.from_json("payload", payload_schema))

    print(df.printSchema())
    print(df.show())

    df_gr = df.groupBy("payload.sensor_id").agg(
        F.avg("payload.modality").alias("avg_modality")
    )
    print(df_gr.show())

    spark.stop()
