from collections import Counter

from hdfs.ext.avro import AvroReader, AvroWriter
from src.client import get_hdfs_client


def main():
    client = get_hdfs_client()

    # Create an AvroWriter instance with the client and file name
    with client.read(
            "/alice-in-wonderland.txt", encoding="utf-8"
    ) as reader, AvroWriter(client, "/word-count.avro", overwrite=True) as writer:
        wordcount = Counter(reader.read().split()).most_common(10)

        # Restructure the wordcount structure, so it now is an array of objects, objects that contain a word and count key
        for key, count in wordcount:
            writer.write({"word": key, "count": count})

    # Read the written file
    with AvroReader(client, "/word-count.avro") as reader:
        schema = reader.schema  # The inferred schema.
        # content = reader.content  # The remote file's HDFS content object.

        # Print the inferred schema
        print(schema)
        print("\n")
        # Print a list of the data
        print(list(reader))


if __name__ == "__main__":
    main()
