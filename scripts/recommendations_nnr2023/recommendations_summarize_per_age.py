"""This script summarizes the extracted csv tables from the Nordic Nutrition Recommendations 2023.

Usage of script DATA_DIR=<path to data directory> python recommendations_summarize_per_age.py
# NOTE: This script is unfinished in its current form.
"""

import csv
import os
from enum import StrEnum
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


class Groups(StrEnum):
    child = "CHILDREN"
    female = "FEMALES"
    male = "MALES"


def get_indiviudal_type(age: str, group: Groups) -> str:
    age = "Lactating" if age == "Lactat\u00ading" else age
    age = "Pregnant" if age == "Preg\u00adnant" else age
    age = age.replace("\u2264", "<=")
    return f"{group.name} ({age})"


def extract_table(file):
    reader = csv.reader(file)
    group = Groups.child  # Child values are at the top of the table
    header = next(reader)
    assert header[0] in ("Age", "Age group", "Agegroup"), "'" + header[0] + "'"
    print(header)  # TODO: prepare header here

    for row in reader:
        match len(row):
            case 1:
                group = Groups(row[0])
                continue
            case _:
                individual_type = get_indiviudal_type(row[0], group)
                print(individual_type)
        # perpare the row data in way that it can later be merged.


if __name__ == "__main__":
    for file_path in (DATA_DIR / "recommendations").glob("*.csv"):
        if not file_path.stem.endswith(("AI", "AR", "PAR", "RI")):
            assert "levels" in file_path.stem
            continue
        with file_path.open("r", encoding="utf-8") as file:
            extract_table(file)

    # Merge all the tables with recommendations
