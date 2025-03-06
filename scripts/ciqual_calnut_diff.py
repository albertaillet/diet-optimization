#!/usr/bin/env -S uv run --script
"""This script compares the ALIM_CODE values between the ciqual and calnut CSV files."""

import csv
import os
from pathlib import Path

DATA_PATH = Path(os.getenv("DATA_DIR", ""))
CIQUAL_CSV = DATA_PATH / "ciqual2020.csv"
CALNUT_0_CSV = DATA_PATH / "calnut.0.csv"
CALNUT_1_CSV = DATA_PATH / "calnut.1.csv"

# Read the column alim_code from the ciqual CSV
ciqual_alim_codes = {row["alim_code"]: row["alim_nom_eng"] for row in csv.DictReader(CIQUAL_CSV.open(), delimiter="\t")}
calnut_0_alim_codes = {row["alim_code"]: row["FOOD_LABEL"] for row in csv.DictReader(CALNUT_0_CSV.open())}
calnut_1_alim_codes = {row["ALIM_CODE"]: row["FOOD_LABEL"] for row in csv.DictReader(CALNUT_1_CSV.open())}

# Check the calnut_0 and calnut_1 have exactly the same ALIM_CODE values
assert calnut_0_alim_codes == calnut_1_alim_codes

# Print the differences between the ciqual and calnut_0
print("ALIM_CODE in ciqual but not in calnut_0:")
sub = set(ciqual_alim_codes) - set(calnut_0_alim_codes)
print(len(sub))
for code in sub:
    print(code, ciqual_alim_codes[code])

print("\nALIM_CODE in calnut_0 but not in ciqual:")
sub = set(calnut_0_alim_codes) - set(ciqual_alim_codes)
print(len(sub))
for code in set(calnut_0_alim_codes) - set(ciqual_alim_codes):
    print(code, calnut_0_alim_codes[code])
