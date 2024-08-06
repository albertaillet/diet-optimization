"""This script summarizes the extracted csv tables from the Nordic Nutrition Recommendations 2023.

Usage of script DATA_DIR=<path to data directory> python recommendations_summarize_general.py
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
        nutrient, unit = row[0].split(", ")
        value_females, value_males, _, _ = row[1:5]
        comment = row[5].replace("\xa0", "")
        assert comment in {"", "AI in NNR2023"}, comment
        RI_or_AI = "AI" if comment == "AI in NNR2023" else "RI"
        assert nutrient not in summary_table
        summary_table[nutrient] = {
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
        nutrient, unit_per_day, value = row
        if nutrient == "Magnesium":
            # NOTE: The UL of Magnesium is currently lower than the AR, so it is skipped.
            # Provisional AR is set to 240 mg/day (females) and 280 mg/day (males).
            # UL is set to 250 mg/day [...] applies only to magnesium in dietary supplements (SCF, 2006).
            # see https://pub.norden.org/nord2023-003/magnesium.html
            continue
        unit, day = unit_per_day.split("/")
        assert day == "d", unit_per_day
        assert nutrient not in upper_intake_table
        upper_intake_table[nutrient] = {"unit": unit, "value_upper_intake": float(value)}
    return upper_intake_table


def fix_micrograms(unit: str) -> str:
    """Both `µ` (MICRO SIGN) and `μ` (GREEK SMALL LETTER MU) are used, setting all to `µ` (MICRO SIGN)."""  # noqa: RUF002
    return unit.replace("μ", "µ")  # noqa: RUF001


def convert_unit(nutrient: str, unit_1: str, unit_2: str) -> tuple[float, float, str]:
    """Convert value_2 with unit_2 to a unit common with unit_1."""
    unit_1 = fix_micrograms(unit_1)
    unit_2 = fix_micrograms(unit_2)
    if unit_1 == unit_2 or (nutrient == "Vitamin A" and unit_1 == "RE" and unit_2 == "µg RE"):  # noqa: RUF001
        return 1, 1, unit_1
    if nutrient == "Vitamin E" and unit_1 == "α-TE" and unit_2 == "mg":  # noqa: RUF001
        # TODO: check correct interpretation of https://en.wikipedia.org/wiki/Vitamin_E#Food_labeling
        # 1 IU is the biological equivalent of about 0.667 mg d (RRR)-alpha-tocopherol (2/3 mg exactly),
        # or of 0.90 mg of dl-alpha-tocopherol, corresponding to the then-measured relative potency of stereoisomers
        # NOTE: assumes mg means mg of IU and I read that α-TE is (RRR)-alpha-tocopherol          # noqa: RUF003
        return 1.5, 1, unit_2
    if nutrient == "Copper" and unit_1 == "µg" and unit_2 == "mg":  # noqa: RUF001
        return 0.001, 1, unit_2
    if unit_1 == "µg" and unit_2 == "mg":  # noqa: RUF001
        return 1, 1000, unit_1
    raise Exception(nutrient, unit_1, unit_2)


def merge_tables(table_1: dict[str, dict[str, Any]], table_2: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    table = {}
    for nutrient in sorted(table_1.keys() | table_2.keys()):
        if nutrient in table_1 and nutrient in table_2:
            unit_1 = table_1[nutrient]["unit"]
            unit_2 = table_2[nutrient]["unit"]
            value_upper_intake = table_2[nutrient]["value_upper_intake"]
            factor_value, factor_upper_intake, unit = convert_unit(nutrient, unit_1, unit_2)
            value_upper_intake = round(factor_upper_intake * value_upper_intake, 1)
            value_males = table_1[nutrient]["value_males"] * factor_value
            assert value_males < value_upper_intake, (value_males, value_upper_intake, nutrient)
            value_females = table_1[nutrient]["value_females"] * factor_value
            assert value_females < value_upper_intake, (value_females, value_upper_intake, nutrient)
            table[nutrient] = {
                "RI_or_AI": table_1[nutrient]["RI_or_AI"],
                "value_males": value_males,
                "value_females": value_females,
                "value_upper_intake": value_upper_intake,
                "unit": unit,
            }
        elif nutrient in table_1:
            table[nutrient] = table_1[nutrient]
        elif nutrient in table_2:
            table[nutrient] = table_2[nutrient]
        else:
            raise KeyError
        table[nutrient]["unit"] = fix_micrograms(table[nutrient]["unit"])
        # Fix potassium to be in mg instead of g.
        if nutrient == "Potassium":
            assert nutrient in table_1 and nutrient not in table_2
            assert table[nutrient]["unit"] == "g"
            table[nutrient]["unit"] = "mg"
            table[nutrient]["value_females"] *= 1000
            table[nutrient]["value_males"] *= 1000
    return table


def to_nutrient_id(nutrient: str) -> str:
    """Renames nutrient names in the tables to the ones present in OFF."""
    return nutrient.lower().replace(" ", "-")


if __name__ == "__main__":
    with (DATA_DIR / "recommendations_nnr2023/levels_comparison_summary.csv").open("r", encoding="utf-8") as file:
        comparison_summary_table = extract_summary_table(file)

    with (DATA_DIR / "recommendations_nnr2023/levels_upper_intake.csv").open("r", encoding="utf-8") as file:
        upper_intake_table = extract_upper_intake_table(file)

    summary_table = merge_tables(comparison_summary_table, upper_intake_table)

    nutrient_cols = "nutrient", "nutrient_id"
    data_cols = "unit", "RI_or_AI", "value_males", "value_females", "value_upper_intake"
    with (DATA_DIR / "recommendations_nnr2023.csv").open("w", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(nutrient_cols + data_cols)
        for nutrient in sorted(summary_table):
            writer.writerow([nutrient, to_nutrient_id(nutrient)] + [summary_table[nutrient].get(col) for col in data_cols])
