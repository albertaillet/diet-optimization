import csv
from pathlib import Path

with Path("calnut.csv").open() as f:
    reader = csv.DictReader(f, delimiter=",")
    nutrients = {row["CONST_LABEL"] for row in reader}
with Path("nutrients.txt").open("w") as f:
    for nutrient in nutrients:
        f.write(nutrient + "\n")
