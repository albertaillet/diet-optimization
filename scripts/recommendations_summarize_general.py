"""This script summarizes the extracted csv tables from the Nordic Nutrition Recommendations 2023.

Usage of script DATA_DIR=<data directory> python scripts/recommendations_summarize.py
"""

import csv
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


def extract_summary_table(file) -> dict[str, dict[str, Any]]:
    reader = csv.reader(file)
    assert next(reader) == ["", "NNR2023", "NNR2012", "Comments"]
    assert next(reader) == ["", "RI or AI", "RI", ""]
    assert next(reader) == ["", "FEMALES", "MALES", "FEMALES", "MALES", ""]
    summary_table = {}
    for row in reader:
        nutirent, unit = row[0].split(", ")
        value_females, value_males, _, _ = row[1:5]
        comment = row[5].replace("\xa0", "")
        assert comment in {"", "AI in NNR2023"}, comment
        RI_or_AI = "AI" if comment == "AI in NNR2023" else "RI"
        assert nutirent not in summary_table
        summary_table[nutirent] = {
            "unit": unit,
            "RI_or_AI": RI_or_AI,
            "value_males": float(value_males),
            "value_females": float(value_females),
        }
    return summary_table


def extract_upper_intake_table(file) -> dict[str, dict[str, Any]]:
    reader = csv.reader(file)
    assert next(reader) == ["", "", "UL per day"]
    upper_intake_table = {}
    for row in reader:
        nutirent, unit_per_day, value = row
        unit, day = unit_per_day.split("/")
        assert day == "d", unit_per_day
        assert nutirent not in upper_intake_table
        upper_intake_table[nutirent] = {"unit": unit, "value_upper_intake": float(value)}
    return upper_intake_table


def convert_unit(unit_1: str, unit_2: str, value_2: float) -> float:
    """Convert value_2 with unit_2 to unit_1."""
    # both `µ` (MICRO SIGN) and `μ` (GREEK SMALL LETTER MU) are used # noqa: RUF003
    unit_2 = unit_2.replace("μ", "µ")  # noqa: RUF001

    if unit_1 == unit_2 or (unit_1 == "RE" and unit_2 == "µg RE"):  # noqa: RUF001
        return value_2
    if unit_1 == "α-TE" and unit_2 == "mg":  # noqa: RUF001
        # TODO: check correct interpretation of https://en.wikipedia.org/wiki/Vitamin_E#Food_labeling
        # 1 IU is the biological equivalent of about 0.667 mg d (RRR)-alpha-tocopherol (2/3 mg exactly),
        # or of 0.90 mg of dl-alpha-tocopherol, corresponding to the then-measured relative potency of stereoisomers
        # NOTE: assumes mg means mg of IU and I read that α-TE is (RRR)-alpha-tocopherol          # noqa: RUF003
        return int(value_2 * 0.667)
    if unit_1 == "µg" and unit_2 == "mg":  # noqa: RUF001
        return 1000 * value_2
    raise Exception(unit_1, unit_2, value_2)


def merge_tables(table_1: dict[str, dict[str, Any]], table_2: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    table = {}
    for nutrient in table_1.keys() | table_2.keys():
        if nutrient in table_1 and nutrient in table_2:
            unit_1 = table_1[nutrient]["unit"]
            unit_2 = table_2[nutrient]["unit"]
            value_2 = table_2[nutrient]["value_upper_intake"]
            table_2[nutrient]["value_upper_intake"] = convert_unit(unit_1, unit_2, value_2)
            table[nutrient] = table_1[nutrient] | table_2[nutrient]
        elif nutrient in table_1:
            table[nutrient] = table_1[nutrient]
        elif nutrient in table_2:
            table[nutrient] = table_2[nutrient]
        else:
            raise KeyError
    return table


if __name__ == "__main__":
    with (DATA_DIR / "recommendations/levels_comparison_summary.csv").open("r", encoding="utf-8") as file:
        comparison_summary_table = extract_summary_table(file)

    with (DATA_DIR / "recommendations/levels_upper_intake.csv").open("r", encoding="utf-8") as file:
        upper_intake_table = extract_upper_intake_table(file)

    summary_table = merge_tables(comparison_summary_table, upper_intake_table)

    header = "nutrient", "unit", "RI_or_AI", "value_males", "value_females", "value_upper_intake"
    with (DATA_DIR / "recommendations.csv").open("w", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        for nutrient, row_data in summary_table.items():
            writer.writerow([nutrient] + [row_data.get(col) for col in header[1:]])
