from pyspark.sql import functions as F
from pyspark.sql import types as T
from src.utils import SPARK_ENV, get_spark_context

if __name__ == "__main__":
    additional_conf = {
        "spark.jars.packages": "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.2"
    }

    # Create a Spark session and context
    spark = get_spark_context(
        app_name="Kafka Streaming",
        app_name="Kafka Streaming",
        config=SPARK_ENV.K8S,
        additional_conf=additional_conf
    )
    sc = spark.sparkContext

    kafka_options = {
        "kafka.bootstrap.servers": "kafka:9092",
        "startingOffsets": "earliest",  # Start from the beginning when we consume from kafka
        "subscribe": "INGESTION",  # Our topic name
    }

    # Read the stream from Kafka topic
    df = spark.readStream.format("kafka").options(**kafka_options).load()
    deserialized_df = df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")

    # Display schema to understand the data structure
    deserialized_df.printSchema()

    # Define the schema for the incoming JSON data
    json_schema = T.StructType([
        T.StructField("correlation_id", T.StringType(), False),
        T.StructField("created_at", T.DoubleType(), False),
        T.StructField("created_at", T.DoubleType(), False),  # Ensure 'created_at' is DoubleType for timestamp conversion
        T.StructField("payload", T.StringType(), False),
        T.StructField("schema_version", T.LongType(), False)
    ])

    payload_schema = T.StructType([
        T.StructField("sensor_id", T.StringType(), False),
        T.StructField("modality", T.FloatType(), False),
        T.StructField("unit", T.StringType(), False),
        T.StructField("temporal_aspect", T.StringType(), False)
    ])

    # Parse the JSON data in the 'value' column
    df_parsed = deserialized_df.withColumn("json_data", F.from_json(F.col("value"), json_schema)).select("json_data.*")


    # Convert 'created_at' to timestamp type
    df_parsed = df_parsed.withColumn("timestamp", F.from_unixtime(F.col("created_at")))

    # Extract the payload JSON and parse it
    df_payload = df_parsed.withColumn("payload", F.from_json(F.col("payload"), payload_schema)).select("timestamp", "payload.*")

    # Calculate the running mean of the 'modality' for each 'sensor_id' using the correct timestamp column
    running_mean = df_payload.groupBy(
        F.window("timestamp", "10 seconds"),  # Use a 10-second window for the running mean
        "sensor_id"
    ).agg(
        F.mean("modality").alias("mean_modality")
    )

    # Define a flag to track if the job should stop
    should_stop = [False]

    def process_batch(batch_df, batch_id):
        """Process each batch and check if the query should stop."""
        # Show the current batch
        batch_df.show(truncate=False)

        # Check a condition to stop the query
        if batch_df.count() > 0:
            should_stop[0] = True

    # Write the result to the console and process each batch using `foreachBatch`
    # Write the result to the console
    query = running_mean.writeStream \
        .outputMode("complete") \
        .foreachBatch(process_batch) \
        .format("console") \
        .option("truncate", "false") \
        .start()

    # Wait for the query to terminate, and stop after processing the first batch
    while query.isActive:
        if should_stop[0]:
            query.stop()
        query.awaitTermination(5)  # Check every 5 seconds
    query.awaitTermination()

    spark.stop()

