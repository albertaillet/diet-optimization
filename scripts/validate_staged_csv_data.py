"""This script validates the csv files data, and is run using pre-commit before they are committed.

Usage of script python validate_staged_csv_data.py <paths to csv files to check>
"""

import csv
import sys
from pathlib import Path

POSSIBLE_UNITS = {"kcal", "g", "mg", "µg", "NE", "RE"}  # noqa: RUF001  # TODO: fix NE and RE


def validate_nutrient_map(reader):
    for row in reader:
        assert row["disabled"] in {"", "TRUE"}
        if row["disabled"]:
            continue
        assert row["id"], row
        assert row["nutrient_type"] in {"micro", "macro"}, row
        assert row["off_id"], row
        assert row["ciqual_id"], row
        assert row["ciqual_name"], row
        if row["nutrient_type"] == "micro":
            assert row["nnr2023_id"], row


def validate_recommendations_macro(reader):
    for row in reader:
        assert row["id"], row
        assert row["unit"] in POSSIBLE_UNITS, row
        assert float(row["value_males"]) >= 0, row
        assert float(row["value_females"]) >= 0, row
        assert float(row["value_upper_intake"]) >= 0, row


def validate_recommendations_nnr2023(reader):
    for row in reader:
        assert row["id"], row
        assert row["unit"] in POSSIBLE_UNITS, row
        assert not row["value_males"] or float(row["value_males"]) >= 0, row
        assert not row["value_females"] or float(row["value_females"]) >= 0, row
        assert not row["value_upper_intake"] or float(row["value_upper_intake"]) >= 0, row


if __name__ == "__main__":
    FILE_PATHS = [Path(p).resolve() for p in sys.argv[1:]]

    for file_path in FILE_PATHS:
        assert file_path.suffix == ".csv"
        if file_path.parent.name == "recommendations_nnr2023":
            continue
        with file_path.open("r") as file:
            reader = csv.DictReader(file)
            match file_path.stem:
                case "nutrient_map":
                    validate_nutrient_map(reader)
                case "recommendations_macro":
                    validate_recommendations_macro(reader)
                case "recommendations_nnr2023":
                    validate_recommendations_nnr2023(reader)
                case _:
                    raise ValueError(f"Unknown staged csv file {file_path}.")
