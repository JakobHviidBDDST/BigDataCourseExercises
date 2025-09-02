from pathlib import Path


def parse_participants(
    filename: Path,
    filename_out: Path = Path("users.txt"),
    prefix: str = "bd-stud",
    course_desc: str = "bd",
):
    """
    Parse the participants file and write to output file.

    :param filename: Input file containing participant data.
    :param filename_out: Output file to write parsed data.
    :param prefix: Prefix to add to each participant's ID.
    :param course_desc: Course description to append to each line.
    """

    with open(filename, "r") as file:
        content = file.readlines()

    content = content[1:]  # Skip the first line
    content = [line.strip() for line in content if line.strip()]
    content = [line.split("\t")[1] for line in content]
    content = [line.removesuffix("@student.sdu.dk") for line in content]
    if prefix:
        content = [f"{prefix}-{line}" for line in content]

    content = [f"{line},{course_desc}-{line}" for line in content]

    with open(filename_out, "w") as file:
        file.write("\n".join(content + [""]))


if __name__ == "__main__":
    parse_participants(Path("./data/its.txt"), Path("tmp-users.txt"))
