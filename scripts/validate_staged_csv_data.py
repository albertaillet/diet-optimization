"""This script validates the csv files data, and is run using pre-commit before they are committed.

Usage of script python validate_staged_csv_data.py <paths to csv files to check>
"""

import csv
import sys
from pathlib import Path

CIQUAL_UNITS = {"kj", "kcal", "g", "mg", "µg"}  # noqa: RUF001
CALNUT_UNITS = {"kj", "kcal", "g", "mg", "mcg"}
MACRO_UNITS = {"kcal", "g", "mg"}
NNR2023_UNITS = {"g", "mg", "mcg", "µg", "NE", "RE"}  # noqa: RUF001  # TODO: fix NE and RE


def validate_nutrient_map(reader):
    for row in reader:
        assert row["id"], row
        assert row["name"], row
        assert row["disabled"] in {"", "TRUE"}, row
        assert row["template"] in {"", "TRUE"}, row
        assert row["nutrient_type"] in {"micro", "macro"}, row
        if row["ciqual_const_code"]:
            assert int(row["ciqual_const_code"]), row
            assert row["ciqual_const_name_eng"], row
            assert row["ciqual_const_name_fr"], row
            assert row["ciqual_unit"] in CIQUAL_UNITS, row
        if row["calnut_const_code"]:
            assert row["calnut_const_code"], row
            assert row["calnut_const_name"], row
            assert row["calnut_unit"] in CALNUT_UNITS, row
            assert int(row["calnut_const_code"]) == int(row["ciqual_const_code"]), row
        if row["disabled"]:
            continue
        assert int(row["ciqual_const_code"]), row
        assert int(row["calnut_const_code"]), row
        if row["off_id"]:
            assert int(row["count"]) > 0, row
        else:
            assert not row["count"], row
        if row["nutrient_type"] == "micro":
            assert row["nnr2023_id"], row


def validate_recommendations_macro(reader):
    for row in reader:
        assert row["id"], row
        assert row["unit"] in MACRO_UNITS, row
        assert float(row["value_males"]) >= 0, row
        assert float(row["value_females"]) >= 0, row
        assert float(row["value_upper_intake"]) >= 0, row


def validate_recommendations_nnr2023(reader):
    for row in reader:
        assert row["nutrient"], row
        assert row["unit"] in NNR2023_UNITS, row
        if row["RI_or_AI"] in {"RI", "AI"}:
            assert float(row["value_males"]) >= 0, row
            assert float(row["value_females"]) >= 0, row
        else:
            assert row["RI_or_AI"] == "", row
            assert not row["value_males"], row
            assert not row["value_females"], row
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
