from src.client import get_hdfs_client


def main():
    # Create a client
    client = get_hdfs_client()
    print("Listing contents of the HDFS root directory:")
    print(client.list("/"))

    print("Reading contents of file /alice-in-wonderland.txt:")
    try:
        # Reading a file, using a delimiter makes it return a list
        with client.read(
                "/alice-in-wonderland.txt", encoding="utf-8", delimiter="\n"
        ) as reader:
            for line in reader:
                print(line)
    except Exception as e:
        print("Failed to read file: " + e.message)

    # Write line(s) to a file
    print("Creating file at /write.txt...")
    with client.write("/write.txt", encoding="utf-8", overwrite=True) as writer:
        writer.write("this is one line of text\n")
        writer.write("this is another line of text\n")

    print("Reading contents of file /write.txt:")
    with client.read("/write.txt", encoding="utf-8", delimiter="\n") as reader:
        for line in reader:
            print(line)


if __name__ == "__main__":
    main()
