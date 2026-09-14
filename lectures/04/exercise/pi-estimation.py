import sys
from operator import add
from random import random

from src.utils import SPARK_ENV, get_spark_context

if __name__ == "__main__":
    """
        Usage: pi [partitions]
    """
    spark = get_spark_context(app_name="Pi estimation", config=SPARK_ENV.LOCAL)
    sc = spark.sparkContext

    partitions = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    n = 1000000 * partitions


    def f(_: int) -> float:
        x = random() * 2 - 1
        y = random() * 2 - 1
        return 1 if x ** 2 + y ** 2 <= 1 else 0


    count = sc.parallelize(range(1, n + 1), partitions).map(f).reduce(add)
    print("Pi is roughly %f" % (4.0 * count / n))

    spark.stop()
