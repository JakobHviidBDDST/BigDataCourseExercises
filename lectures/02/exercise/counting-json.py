from collections import Counter
from json import dumps

from src.client import get_hdfs_client


def main():
    client = get_hdfs_client()

    with client.read("/alice-in-wonderland.txt", encoding="utf-8") as reader:
        # Using Python's collections' Counter to count occurences of a word in a string, and return the 10 most common
        wordcount = Counter(reader.read().split()).most_common(10)

        # One line write a file, with a dump (=JSON formatted) of the wordcount structure
        client.write(
            "/word-count.json", dumps(wordcount), encoding="utf-8", overwrite=True
        )


if __name__ == "__main__":
    main()
