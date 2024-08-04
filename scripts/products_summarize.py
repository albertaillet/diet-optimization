"""This script summarizes the fetched product information into a csv file.

Usage of script DATA_DIR=<data directory> python scripts/products_summarize.py
"""

import csv
import json
import os
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


ALL_ESTIMATED_NUTRIENTS = [
    "alcohol",
    "beta-carotene",
    "calcium",
    "carbohydrates",
    "cholesterol",
    "copper",
    "energy-kcal",
    "energy-kj",
    "energy",
    "fat",
    "fiber",
    "folate",
    "fructose",
    "galactose",
    "glucose",
    "iodine",
    "iron",
    "lactose",
    "magnesium",
    "maltose",
    "manganese",
    "niacin",
    "pantothenic-acid",
    "phosphorus",
    "phylloquinone",
    "polyols",
    "potassium",
    "proteins",
    "riboflavin",
    "salt",
    "saturated-fat",
    "selenium",
    "sodium",
    "starch",
    "sucrose",
    "sugars",
    "thiamin",
    "vitamin-a",
    "vitamin-b12",
    "vitamin-b6",
    "vitamin-c",
    "vitamin-d",
    "vitamin-e",
    "vitamin-pp",
    "water",
    "zinc",
]

# The nutrition estimation of OFF is located here.
# https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionCiqual.pm
# https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionEstimation.pm
# The consulted repository version is available using the same URL, but replacing main with the permalink:
# main -> ab5c4410cd0f3017803cdfe4304f91dfa7636034

# None discards the column while a key gives it a custom key.
HARDCODED = {
    "Energy, Regulation EU No 1169/2011": "energy",
    "Energy, N x Jones' factor, with fibres": None,
    "Protein": "proteins",
    "Protein, crude, N x 6.25": None,
    "Carbohydrate": "carbohydrates",
    "Fibres": "fiber",
    "Ash": None,
    "Organic acids": None,
    "FA saturated": "saturated-fat",
    "FA mono": None,
    "FA poly": None,  # fa-poly
    "FA 4:0": None,  # fa-4:0
    "FA 6:0": None,  # fa-6:0
    "FA 8:0": None,  # fa-8:0
    "FA 10:0": None,  # fa-10:0
    "FA 12:0": None,  # fa-12:0
    "FA 14:0": None,  # fa-14:0
    "FA 16:0": None,  # fa-16:0
    "FA 18:0": None,  # fa-18:0
    "FA 18:1 n-9 cis": None,  # fa-18:1-n-9-cis
    "FA 18:2 9c,12c (n-6)": None,  # fa-18:2-9c,12c-(n-6)
    "FA 18:3 c9,c12,c15 (n-3)": None,  # fa-18:3-c9,c12,c15-(n-3)
    "FA 20:4 5c,8c,11c,14c (n-6)": None,  # fa-20:4-5c,8c,11c,14c-(n-6)
    "FA 20:5 5c,8c,11c,14c,17c (n-3) EPA": None,  # fa-20:5-5c,8c,11c,14c,17c-(n-3)-epa
    "FA 22:6 4c,7c,10c,13c,16c,19c (n-3) DHA": None,  # fa-22:6-4c,7c,10c,13c,16c,19c-(n-3)-dha
    "Chloride": None,  # chloride
    "Retinol": None,  # retinol
    "Vitamin K1": None,  # vitamin-k1  # TODO: incorporate k vitamins in the future as they are in recommendations
    "Vitamin K2": None,  # vitamin-k2
}


def make_price_per_kg(item: dict[str, Any]) -> float | None:
    """Make the price per 1kg."""
    product_identification = f"{item['product_code']}, {item['product']['product_name']}"

    # Check that product_quantity is available.
    product_quantity = item["product"]["product_quantity"]
    if product_quantity is None:
        print("Missing product_quantity:", product_identification)
        return None

    # Check that the product quantity is larger than zero.
    product_quantity_numerical = float(product_quantity)
    if product_quantity_numerical <= 0:
        print("Zero product_quantity:", product_identification)
        return None

    # Check that the product_quantity_unit is in g.
    # NOTE: it is assumed that it is grams if not available
    product_quantity_unit = item["product"]["product_quantity_unit"]
    if product_quantity_unit is None:
        print("Missing product_quantity_unit:", product_identification)
        product_quantity_unit = "g"
    assert product_quantity_unit == "g", product_identification

    return 1000 * float(item["price"]) / product_quantity_numerical


def fix_micrograms(unit: str) -> str:
    """Both `µ` (MICRO SIGN) and `μ` (GREEK SMALL LETTER MU) are used, setting all to `µ` (MICRO SIGN)."""  # noqa: RUF002
    return unit.replace("μ", "µ")  # noqa: RUF001


def create_prices_lookup(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    prices_lookup = {}
    for item in items:
        # Get price per kg and skip the price if it returns None.
        price = make_price_per_kg(item)
        if item["product_code"] in prices_lookup:
            print("DUPLICATE", item["product_code"])
            continue
        prices_lookup[item["product_code"]] = {
            "currency": item["currency"],
            "price": price,
            "price_date": item["date"],
            "location": item["location"]["osm_name"],
            "location_osm_id": item["location"]["osm_id"],
        }
    return prices_lookup


def adapt_ciqual_column_name(name: str) -> str | None:
    if name in HARDCODED:
        new_name = HARDCODED[name]
        if new_name is None:
            return None
    else:
        new_name = name.lower()
        if " or " in new_name:
            new_name = new_name.split(" or ")[1]
        new_name = new_name.replace(" ", "-")
    assert new_name in ALL_ESTIMATED_NUTRIENTS, (name, new_name)
    return new_name


def get_ciqual_nutrient_keys(header: list[str]) -> dict[str, tuple[str, str]]:
    """Extract which columns to keep and match the keys to those from OFF (see all_estimated_nutrients)."""
    key_pattern = re.compile(r"(.+)\s+\(((\w*g)|kj|kcal)\/100g\)")
    nutrient_keys = {}
    for col in header:
        pattern_match = key_pattern.match(col)
        if pattern_match is None:
            continue
        name = pattern_match.group(1)
        unit = fix_micrograms(pattern_match.group(2))  # TODO: check that the right unit is used.
        new_col = adapt_ciqual_column_name(name)
        if new_col is None:
            continue
        nutrient_keys[col] = (new_col, unit)
    return nutrient_keys


def to_value(value: str) -> float | None:
    """Transform the ciqual string values to numerical values."""
    # Replace comma with dots 2,4 -> 2.4
    value = value.replace(",", ".")
    # Set unknown values to None
    if value in {"", "-"}:
        return 0
    # Set values with traces to 0. Similar to:
    # https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionCiqual.pm#L194
    if "traces" in value:
        return 0.0
    # Set values with < to their upper bound
    # NOTE: There could be a better way to do this, as this overestimates certain nutrients.
    if "<" in value:
        return float(value.replace("<", ""))
    return float(value)


def load_ciqual_database(file) -> dict[str, dict[str, Any]]:
    reader = csv.reader(file, delimiter="\t")
    header = next(reader)
    nutrient_keys = get_ciqual_nutrient_keys(header)

    ciqual_data = {}
    for row in reader:
        row = dict(zip(header, row, strict=True))
        ciqual_id = row["alim_code"]
        ciqual_data[ciqual_id] = {"ciqual_name": row["alim_nom_eng"]}
        for col, (new_col, col_unit) in nutrient_keys.items():
            ciqual_data[ciqual_id][new_col + "_value"] = to_value(row[col])
            ciqual_data[ciqual_id][new_col + "_unit"] = col_unit
    return ciqual_data


def create_nutrient_row(
    reported_nutrients: dict[str, float | str], ciqual_nutrients: dict[str, float | str]
) -> dict[str, float | str]:
    nutrients = {}
    for nurtient_name in ALL_ESTIMATED_NUTRIENTS:
        nurtient_value = nurtient_name + "_value"
        nurtient_unit = nurtient_name + "_unit"
        nutrient_source = nurtient_name + "_source"
        if nurtient_name in reported_nutrients:
            nutrients[nurtient_value] = reported_nutrients[nurtient_name]
            nutrients[nurtient_unit] = reported_nutrients[nurtient_unit]
            nutrients[nutrient_source] = "reported"
        elif nurtient_value in ciqual_nutrients:
            nutrients[nurtient_value] = ciqual_nutrients[nurtient_value]
            nutrients[nurtient_unit] = ciqual_nutrients[nurtient_unit]
            nutrients[nutrient_source] = "ciqual"
    return nutrients


def create_csv(
    file, items: list[dict[str, Any]], ciqual_lookup: dict[str, dict[str, Any]], prices_dict: dict[str, dict[str, Any]]
):
    product_cols = ["product_code", "product_name", "ciqual_code", "ciqual_name"]
    price_cols = ["price", "currency", "price_date", "location", "location_osm_id"]
    nutrient_cols = [name + suffix for name in ALL_ESTIMATED_NUTRIENTS for suffix in ("_value", "_unit", "_source")]
    header = product_cols + price_cols + nutrient_cols

    writer = csv.writer(file)
    writer.writerow(header)  # Write the header

    # Write the data rows
    for item in items:
        reported_nutrients = item["product"]["nutriments"]

        # NOTE: The OFF estimated nutrients in item["product"].get("nutriments_estimated")
        # are not used as the units have not been checked.

        # NOTE: when the ciqual_food_code:en is not available, the agribalyse_food_code:en or agribalyse_proxy_food_code:en is
        # used instead, which may not really match the true nutritional values of the product.
        ciqual_code = item["product"]["categories_properties"].get("ciqual_food_code:en")
        if ciqual_code is None:
            ciqual_code = item["product"]["categories_properties"].get("agribalyse_food_code:en")
        if ciqual_code is None:
            ciqual_code = item["product"]["categories_properties"].get("agribalyse_proxy_food_code:en")
        ciqual_nutrients = ciqual_lookup[ciqual_code] if ciqual_code is not None else {}
        ciqual_name = ciqual_lookup[ciqual_code]["ciqual_name"] if ciqual_code is not None else None

        nutrients = create_nutrient_row(reported_nutrients, ciqual_nutrients)

        row_dict = {
            "product_name": item["product"].get("product_name"),
            "product_code": item["code"],
            "ciqual_code": ciqual_code,
            "ciqual_name": ciqual_name,
            **prices_dict[item["code"]],
            **nutrients,
        }
        writer.writerow([row_dict.get(col) for col in header])


if __name__ == "__main__":
    with (DATA_DIR / "prices.json").open("r") as file:
        prices = json.load(file)
    prices_dict = create_prices_lookup(prices["items"])

    with (DATA_DIR / "products.json").open("r") as file:
        products = json.load(file)

    with (DATA_DIR / "ciqual2020.csv").open("r") as file:
        ciqual_lookup = load_ciqual_database(file)

    with (DATA_DIR / "product_prices_and_nutrients.csv").open("w", newline="", encoding="utf-8") as file:
        create_csv(file, products, ciqual_lookup, prices_dict)
