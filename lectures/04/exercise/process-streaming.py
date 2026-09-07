from src.utils import SPARK_ENV, get_spark_context

if __name__ == "__main__":
    # Create a Spark session and context
    spark = get_spark_context(app_name="Kafka Streaming", config=SPARK_ENV.K8S)
    sc = spark.sparkContext

    kafka_options = {
        "kafka.bootstrap.servers": "kafka:9092",
        "startingOffsets": "earliest",  # Start from the beginning when we consume from kafka
        "subscribe": "INGESTION",  # Our topic name
    }

    df = spark.readStream.format("kafka").options(**kafka_options).load()
    deserialized_df = df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")

    # TODO - create your logic
    # streaming_df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")

    spark.stop()
