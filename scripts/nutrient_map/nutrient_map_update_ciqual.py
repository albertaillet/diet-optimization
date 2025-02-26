"""This script adds all the ciqual const information to the nutrient_map.csv."""

import csv
import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

if __name__ == "__main__":
    nutrient_map = DATA_DIR / "nutrient_map.csv"
    ciqual_const = DATA_DIR / "ciqual2020/const.csv"

    # const_code, const_nom_fr, const_nom_eng
    with ciqual_const.open() as f:
        reader = csv.DictReader(f)
        code_to_name = {row["const_code"]: (row["const_nom_fr"], row["const_nom_eng"]) for row in reader}

    new_nutrient_map = []
    with nutrient_map.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            new_nutrient_map.append(row)
            code = row["calnut_const_code"]
            if code not in code_to_name:
                print(f"Missing const code: {code}")
                continue
            row["ciqual_const_code"] = code
            row["ciqual_const_name_fr"], row["ciqual_const_name_eng"] = code_to_name.pop(code)
    fieldnames = [
        "id",
        "name",
        "ciqual_const_code",
        "ciqual_const_name_eng",
        "ciqual_const_name_fr",
        "ciqual_unit",
        "calnut_const_code",
        "calnut_const_name",
        "calnut_unit",
        "off_id",
        "count",
        "template",
        "nnr2023_id",
        "nutrient_type",
        "disabled",
        "comments",
    ]
    with nutrient_map.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)  # type: ignore
        writer.writeheader()
        writer.writerows(new_nutrient_map)

    print("Updated nutrient_map.csv!")
    if code_to_name:
        print("Missing codes:")
        for code, (name_fr, name_eng) in code_to_name.items():
            print(f"{code}: {name_fr}, {name_eng}")
