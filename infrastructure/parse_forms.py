from pathlib import Path

import pandas as pd


def parse_participants(
    filename: Path,
    filename_ref: Path,
    filename_out: Path,
):
    """
    Parse the participants file and write to output file.

    :param filename: Input file containing participant data.
    :param filename_out: Output file to write parsed data.
    :param prefix: Prefix to add to each participant's ID.
    :param course_desc: Course description to append to each line.
    """

    column_names = [
        "Id",
        "Start time",
        "Completion time",
        "Email",
        "Name",
        "SDU student mail 1",
        "SDU student mail 2",
        "SDU student mail 3",
        "SDU student mail 4",
        "SDU student mail 5",
        "SDU student mail 6",
    ]
    column_keep = column_names[:1] + [
        i for i in column_names if i.startswith("SDU student mail")
    ]
    df = pd.read_csv(filename, sep=";", header=None)
    df.columns = column_names
    df = df[column_keep]
    # Assuming df is already loaded and columns are set
    student_mail_cols = [
        col for col in df.columns if col.startswith("SDU student mail")
    ]
    df = df.melt(
        id_vars=["Id"],
        value_vars=student_mail_cols,
        var_name="student",
        value_name="student_mail",
    )
    df = df.dropna()
    df["student_mail"] = df["student_mail"].apply(lambda x: x.lower())
    df["student"] = df["student_mail"].apply(lambda x: x.split("@")[0])

    # Fjern Henrik
    henrik_id = "hebas16"
    df = df.loc[~df["student_mail"].apply(lambda x: x.startswith(henrik_id))]

    print("Students pr. group")
    print(df.groupby("Id", as_index=False).size())

    # find missing

    with open(filename_ref, mode="r") as f:
        users = f.read().splitlines()

    print("Students missing a group")
    users = set([u.split("-")[-1] for u in users])
    users.remove(henrik_id)
    print(users - set(df["student"].to_list()))

    df_gr = df.groupby("Id", as_index=False).agg({"student": lambda x: ", ".join(x)})
    df_gr.to_csv(filename_out, index=False)


if __name__ == "__main__":
    parse_participants(
        Path(
            "./data/E25 Big data and data science technologies_ Project groups(Sheet1).csv"
        ),
        Path("users.txt"),
        Path("./data/project_groups.csv"),
    )
