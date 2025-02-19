"""This script summarizes the fetched product information into a csv file.

Usage of script DATA_DIR=<path to data directory> OFF_USERNAME=<yourusername> python products_summarize.py

NOTE: This file could be simplified by first creating intermediary tables and then using inner_merge.
"""

import csv
import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))
OFF_USERNAME = os.getenv("OFF_USERNAME")


def make_price_per_kg_or_l(price_item: dict[str, Any], product_item: dict[str, Any]) -> float | None:
    """Make the price per 1kg or 1L."""
    product_identification = f"{price_item['product_code']}, {price_item['product']['product_name']}"

    # Check that product_quantity is available.
    product_reported_quantity = product_item["product"].get("product_quantity")
    price_reported_quantity = price_item["product"]["product_quantity"]
    if product_reported_quantity is None and price_reported_quantity is None:
        print("Missing product_quantit:", product_identification)
        return None
    if price_reported_quantity is None:
        print("Missing product_quantity in price:", product_identification)
        quantity = float(product_reported_quantity)
    elif product_reported_quantity is None:
        print("Missing product_quantity in product:", product_identification)
        quantity = float(price_reported_quantity)
    elif float(product_reported_quantity) != float(price_reported_quantity):
        print("WARNING product quantity mismatch", price_reported_quantity, product_reported_quantity, product_identification)
        # NOTE: Taking the smallest value if they differ
        quantity = min(float(price_reported_quantity), float(product_reported_quantity))
    elif float(product_reported_quantity) == float(price_reported_quantity):
        quantity = float(product_reported_quantity)
    else:
        raise ValueError("Unreachable branch reached")

    # Check that the quantity is larger than zero.
    if quantity <= 0:
        print("Zero product_quantity:", product_identification, quantity)
        return None

    product_quantity_unit = product_item["product"].get("product_quantity_unit")
    price_quantity_unit = price_item["product"]["product_quantity_unit"]
    # NOTE: sometime the product_quantity_unit is available in product_item but not in price_item
    if product_quantity_unit != price_quantity_unit:
        print("Mismatch unit", price_quantity_unit, product_quantity_unit, product_identification)

    # NOTE: using quantity unit reported in product
    quantity_unit = product_quantity_unit
    if product_quantity_unit is None:
        print("Missing product_quantity_unit:", product_identification)
        # NOTE: it is assumed that it is grams if not available
        quantity_unit = "g"

    # Check that the unit is either grams or ml
    assert quantity_unit in {"g", "ml"}, product_identification

    # Divide the price by the quantity, multiply by 1000 and round to 2 decimals.
    return round(1000 * float(price_item["price"]) / quantity, 2)


def ciqual_entry_to_value(value: str) -> float:
    """Transform the ciqual string values to numerical values."""
    # Replace comma with dots 2,4 -> 2.4
    value = value.replace(",", ".")
    # Set unknown values to 0.
    if value in {"", "-"}:
        return 0
    # Set values with traces to 0. Similar to:
    # https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionCiqual.pm#L194
    if "traces" in value:
        return 0.0
    # Set values with < to their upper bound divided by two.
    # Same method as in the CIQUAL CALNUT table
    # https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20CALNUT%202020_doc_FR_2020%2007%2007.pdf
    # NOTE: There could be a better way to do this, as this may give a wrong estimation of nutrients.
    if "<" in value:
        return float(value.replace("<", "")) / 2
    return float(value)


def ciqual_load_table(file, nutrient_map: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    ciqual_table = {}
    for ciqual_row in csv.DictReader(file, delimiter="\t"):
        ciqual_code = ciqual_row["alim_code"]
        ciqual_table[ciqual_code] = {"ciqual_code": ciqual_row["alim_code"], "ciqual_name": ciqual_row["alim_nom_eng"]}
        for nmr in nutrient_map:
            nutrient_id = nmr["id"]
            ciqual_table[ciqual_code][nutrient_id + "_value"] = ciqual_entry_to_value(ciqual_row[nmr["ciqual_id"]])
            ciqual_table[ciqual_code][nutrient_id + "_unit"] = nmr["ciqual_unit"]
    return ciqual_table


def create_nutrient_row(
    reported_nutrients: dict[str, float | str], ciqual_nutrients: dict[str, float | str], nutrient_map: list[dict[str, str]]
) -> dict[str, float | str]:
    nutrients = {}
    for nutrient_map_row in nutrient_map:
        nutrient_id = nutrient_map_row["id"]
        nurtient_value = nutrient_id + "_value"
        nurtient_unit = nutrient_id + "_unit"
        nutrient_source = nutrient_id + "_source"
        if nurtient_value in reported_nutrients:
            nutrients[nurtient_value] = reported_nutrients[nurtient_value]
            nutrients[nurtient_unit] = reported_nutrients[nurtient_unit]
            nutrients[nutrient_source] = "reported"
        elif nurtient_value in ciqual_nutrients:
            nutrients[nurtient_value] = ciqual_nutrients[nurtient_value]
            nutrients[nurtient_unit] = ciqual_nutrients[nurtient_unit]
            nutrients[nutrient_source] = "ciqual"
    return nutrients


def create_csv(
    file,
    price_items: list[dict[str, Any]],
    products_dict: dict[str, dict[str, Any]],
    ciqual_table: dict[str, dict[str, Any]],
    nutrient_map: list[dict[str, str]],
):
    product_cols = ["product_code", "product_name", "ciqual_code", "ciqual_name"]
    price_cols = ["price", "currency", "price_date", "location", "location_osm_id"]
    nutrient_cols = [d["id"] + suffix for d in nutrient_map for suffix in ("_value", "_unit", "_source")]
    header = ["id", *product_cols, *price_cols, *nutrient_cols]

    writer = csv.writer(file)
    writer.writerow(header)  # Write the header

    # Write the data rows
    for price_item in price_items:
        product_code = price_item["product_code"]
        if product_code not in products_dict:
            print(product_code, "not found in products_dict")
            continue
        product_item = products_dict[product_code]

        if "product" not in product_item:
            print(product_code, " missing product key")
            continue
        reported_nutrients = product_item["product"]["nutriments"]

        # NOTE: The OFF estimated nutrients in item["product"].get("nutriments_estimated")
        # are not used as the units have not been checked.

        # NOTE: when the ciqual_food_code:en is not available, the agribalyse_food_code:en or agribalyse_proxy_food_code:en is
        # used instead, which may not really match the true nutritional values of the product.
        ciqual_code = product_item["product"]["categories_properties"].get("ciqual_food_code:en")
        if ciqual_code is None:
            ciqual_code = product_item["product"]["categories_properties"].get("agribalyse_food_code:en")
        if ciqual_code is None:
            ciqual_code = product_item["product"]["categories_properties"].get("agribalyse_proxy_food_code:en")

        ciqual_name = None
        ciqual_nutrients = ciqual_table.get(ciqual_code, {})
        if ciqual_nutrients == {}:
            print("ciqual_code", ciqual_code, "is missing for product", product_code, product_item["product"].get("product_name"))
        else:
            ciqual_name = ciqual_table[ciqual_code]["ciqual_name"] if ciqual_code is not None else None

        row_dict = {
            "id": price_item["id"],
            "product_name": product_item["product"].get("product_name"),
            "product_code": product_item["code"],
            "ciqual_code": ciqual_code,
            "ciqual_name": ciqual_name,
            "currency": price_item["currency"],
            "price": make_price_per_kg_or_l(price_item, product_item),
            "price_date": price_item["date"],
            "location": price_item["location"]["osm_name"],
            "location_osm_id": price_item["location"]["osm_id"],
            **create_nutrient_row(reported_nutrients, ciqual_nutrients, nutrient_map),
        }
        writer.writerow([row_dict.get(col) for col in header])


if __name__ == "__main__":
    assert OFF_USERNAME is not None, f"Set OFF_USERNAME env variable {OFF_USERNAME=}"

    with (DATA_DIR / "user_data" / OFF_USERNAME / "prices.json").open("r") as file:
        price_items = json.load(file)["items"]

    with (DATA_DIR / "user_data" / OFF_USERNAME / "products.json").open("r") as file:
        products_dict = json.load(file)

    with (DATA_DIR / "nutrient_map.csv").open("r") as file:
        nutrient_map = [nmr for nmr in csv.DictReader(file) if nmr["ciqual_id"] and nmr["id"]]

    with (DATA_DIR / "ciqual2020.csv").open("r") as file:
        ciqual_table = ciqual_load_table(file, nutrient_map)

    with (DATA_DIR / "user_data" / OFF_USERNAME / "product_prices_and_nutrients.csv").open("w") as file:
        create_csv(file, price_items, products_dict, ciqual_table, nutrient_map)
