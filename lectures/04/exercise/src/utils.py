"""
This module contains utility functions for the Spark applications.
"""

import locale
import os
import re
import subprocess
from enum import Enum

from pyspark import SparkConf
from pyspark.sql import SparkSession

locale.getdefaultlocale()
locale.getpreferredencoding()

FS: str = "hdfs://namenode:9000/"
# Get the IP address of the host machine.
SPARK_DRIVER_HOST = (
    subprocess.check_output(["hostname", "-i"]).decode(encoding="utf-8").strip()
)

SPARK_DRIVER_HOST = re.sub(rf"\s*127.0.0.1\s*", "", SPARK_DRIVER_HOST)
os.environ["SPARK_LOCAL_IP"] = SPARK_DRIVER_HOST


class SPARK_ENV(Enum):
    LOCAL = [
        ("spark.master", "local"),
        ("spark.driver.host", SPARK_DRIVER_HOST),
    ]
    K8S = [
        ("spark.master", "spark://spark-master-svc:7077"),
        ("spark.driver.bindAddress", "0.0.0.0"),
        ("spark.driver.host", SPARK_DRIVER_HOST),
        ("spark.driver.port", "7077"),
        ("spark.submit.deployMode", "client"),
    ]


def get_spark_context(app_name: str, config: SPARK_ENV, additional_conf: dict = None) -> SparkSession:
    """Get a Spark context with the given configuration and optional additional configurations."""
    spark_conf = SparkConf().setAll(config.value).setAppName(app_name)

    # Apply additional configurations if provided
    if additional_conf:
        spark_conf.setAll(additional_conf.items())

    return SparkSession.builder.config(conf=spark_conf).getOrCreate()
