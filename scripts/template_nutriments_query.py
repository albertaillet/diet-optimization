import csv
import os
from pathlib import Path

DATA_PATH = Path(os.getenv("DATA_PATH", "data"))
CSV_FILE = DATA_PATH / "nutrient_map.csv"
nutrients = [row["off_id"] for row in csv.DictReader(CSV_FILE.open()) if row["off_id"] and not row["disabled"]]

# Build rows as lists of strings (each column as a separate string)
rows = [
    (f"'{nutrient}',", f'p.nutriments."{nutrient}_value",', f'p.nutriments."{nutrient}_unit",', f'p.nutriments."{nutrient}_100g"')
    for nutrient in nutrients
]

# Calculate the maximum width for each column across all rows
col_widths = [max(len(row[i]) for row in rows) for i in range(4)]

# Format and print each row with aligned columns
for row in rows:
    formatted_row = "({col1:<{w1}}{col2:<{w2}}{col3:<{w3}}{col4:<{w4}}),".format(
        col1=row[0], col2=row[1], col3=row[2], col4=row[3], w1=col_widths[0], w2=col_widths[1], w3=col_widths[2], w4=col_widths[3]
    )
    print(formatted_row)
