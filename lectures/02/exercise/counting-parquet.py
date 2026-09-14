from collections import Counter

import pandas as pd
from src.client import get_hdfs_client


def main():
    client = get_hdfs_client()

    with client.read("/alice-in-wonderland.txt", encoding="utf-8") as reader:
        wordcount = Counter(reader.read().split())

        df = pd.DataFrame.from_dict(dict(wordcount), orient="index").transpose()
        df.to_parquet("/word-count.parquet")

        client.upload("/word-count.parquet", "/word-count.parquet", overwrite=True)

    with client.read("/word-count.parquet", encoding="utf-8") as reader:
        df = pd.read_parquet("/word-count.parquet")
        print(df)


if __name__ == "__main__":
    main()
