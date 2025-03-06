#!/usr/bin/env -S uv run --script
"""This script validates the csv files data, and is run using pre-commit before they are committed."""

import csv
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CIQUAL_CONST_PATH = DATA_DIR / "ciqual2020/const.csv"
CALNUT_1_PATH = DATA_DIR / "calnut.1.csv"


CIQUAL_UNITS = {"kj", "kcal", "g", "mg", "µg"}  # noqa: RUF001
CALNUT_UNITS = {"kj", "kcal", "g", "mg", "mcg"}
MACRO_UNITS = {"kcal", "g", "mg"}
NNR2023_UNITS = {"g", "mg", "mcg", "µg", "NE", "RE"}  # noqa: RUF001  # TODO: fix NE and RE


def get_ciqual_const_codes():
    if not CIQUAL_CONST_PATH.exists():
        exit("Warning: CIQUAL data not found, plase fetch it using `make unzip_and_process_ciqual`.")
    with CIQUAL_CONST_PATH.open("r") as f:
        return {row["const_code"]: row for row in csv.DictReader(f)}


def get_calnut_const_codes():
    if not CALNUT_1_PATH.exists():
        exit("Warning: CALNUT data not found, plase fetch it using `make data/calnut.1.csv`.")
    with CALNUT_1_PATH.open("r") as f:
        return {row["CONST_CODE"]: row["CONST_LABEL"] for row in csv.DictReader(f)}


def validate_nutrient_map(reader):
    ciqual_const_codes = get_ciqual_const_codes()
    calnut_const_codes = get_calnut_const_codes()

    for row in reader:
        assert row["id"], row
        assert row["name"], row
        assert row["disabled"] in {"", "TRUE"}, row
        assert row["template"] in {"", "TRUE"}, row
        assert row["nutrient_type"] in {"micro", "macro"}, row
        if row["ciqual_const_code"]:
            assert int(row["ciqual_const_code"]), row  # Check that the ciqual_const_code is a non-zero integer
            assert row["ciqual_const_name_eng"], row
            assert row["ciqual_const_name_fr"], row
            assert row["ciqual_unit"] in CIQUAL_UNITS, row
            # Check that the ciqual_const_code in the const.csv file are present in the nutrient_map.csv
            assert row["ciqual_const_code"] in ciqual_const_codes, row
            ciqual_row = ciqual_const_codes[row["ciqual_const_code"]]
            assert row["ciqual_const_name_eng"] == ciqual_row["const_nom_eng"], (row, ciqual_row)
            assert row["ciqual_const_name_fr"] == ciqual_row["const_nom_fr"], (row, ciqual_row)
        else:
            assert not row["ciqual_const_name_eng"], row
            assert not row["ciqual_const_name_fr"], row
            assert not row["ciqual_unit"], row
        if row["calnut_const_code"]:
            assert row["calnut_const_code"], row
            assert row["calnut_const_name"], row
            assert row["calnut_unit"] in CALNUT_UNITS, row
            assert int(row["calnut_const_code"]) == int(row["ciqual_const_code"]), row
            assert row["calnut_const_code"] in calnut_const_codes, row
            *name, unit = calnut_const_codes[row["calnut_const_code"]].split("_")
            assert row["calnut_const_name"] == "_".join(name), row
            assert row["calnut_unit"] == unit, row
        else:
            assert not row["calnut_const_name"], row
            assert not row["calnut_unit"], row
        if row["off_id"]:
            assert int(row["count"]) > 0, row
        else:
            assert not row["count"], row
        if row["disabled"]:
            continue
        assert int(row["ciqual_const_code"]), row
        assert int(row["calnut_const_code"]), row
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
