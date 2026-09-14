""" HDFS client module """

from hdfs import InsecureClient

HDFS_HOST: str = "http://namenode:9870"
HDFS_USER_NAME: str = "root"


def get_hdfs_client(
    url: str = HDFS_HOST, username: str = HDFS_USER_NAME
) -> InsecureClient:
    """Get an HDFS client"""
    return InsecureClient(url=url, user=username)
