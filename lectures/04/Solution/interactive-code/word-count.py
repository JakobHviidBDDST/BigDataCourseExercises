import sys
from operator import add

from src.utils import FS, SPARK_ENV, get_spark_context

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: wordcount <file>", file=sys.stderr)
        sys.exit(-1)

    spark = get_spark_context(app_name="Word Count", config=SPARK_ENV.K8S)
    sc = spark.sparkContext

    # Read file line by line
    lines = sc.textFile(f"{FS}{sys.argv[1]}")  # .rdd.map(lambda r: r[0])
    # Split each line at spaces (splits it into words)
    words = lines.flatMap(lambda x: x.split(" "))
    # Map each word to a tuple (word, 1)
    tuples = words.map(lambda x: (x, 1))
    # Reduce tuples by key (word) which results in a list of tuples with unique words and their total counts
    sums = tuples.reduceByKey(add)
    # Sort the list of tuples by the second element (count) in descending order
    sorted = sums.sortBy(lambda x: x[1], ascending=False)

    # Convert the sorted data to a DataFrame
    result_df = sorted.toDF(schema=["word", "count"])

    # Save the result to a JSON file
    writer = result_df.write.mode("overwrite")
    writer.json(f"{FS}word-count.json")

    # Take the first 10 elements of the list
    top_10 = sorted.take(10)
    # Print the top 10 words and their counts
    print(f"Top 10 words in {sys.argv[1]} are:")
    for word, count in top_10:
        print("%s: %i" % (word, count))

    spark.stop()
