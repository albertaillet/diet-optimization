"""This script combines the different summarized csv files and creates a dashboard to interact
with linear optimization to get the optimal quantities of food products.

Usage of script DATA_DIR=<path to data directory> OFF_USERNAME=<yourusername> python app.py

TODO: show/hide sliders depending on the chosen nutrients.
TODO: have link to load info card for each of the chosen products.

Long term todos:
- Retrieve prices in SQL database.
- User authenticaiton.

Todos from dash dashboard
TODO: Include other objectives than price minimization with tunable hyperparameters.
TODO: Choose to include maximum values even when they are not available in recommendations.
TODO: Include breakdown source of each nutrient (either in popup, other page or in generated pdf).
"""

import csv
import math
import os
from pathlib import Path

import numpy as np
from flask import Flask, render_template, request
from scipy.optimize import linprog

from utils.table import inner_merge

DEBUG = os.getenv("DEBUG")
DATA_DIR = Path(os.getenv("DATA_DIR", ""))
OFF_USERNAME = os.getenv("OFF_USERNAME")
POSSIBLE_CURRENCIES = ["EUR", "CHF"]


def load_and_filter_products(file, used_nutrients: list[str]) -> dict[str, list[str | float]]:
    """Filters to only the relevant nutrients and drops all products with missing values."""
    product_cols = {"product_code": str, "product_name": str, "ciqual_code": str, "ciqual_name": str}
    price_cols = {"price": float, "currency": str, "price_date": str, "location": str, "location_osm_id": str}
    nutrient_cols = {
        name + suffix: _type for name in used_nutrients for suffix, _type in (("_value", float), ("_unit", str), ("_source", str))
    }
    cols = product_cols | price_cols | nutrient_cols

    products = {col: [] for col in cols}  # Column-oriented dict.
    for row in csv.DictReader(file):
        # Filter out rows where any values are missing.
        if any(row[col] == "" for col in cols):
            continue
        # Filter out rows with unsupported currencies.
        if row["currency"] not in POSSIBLE_CURRENCIES:
            continue
        # Append each of the row values to the correct col, while casting it to _type.
        for col, _type in cols.items():
            products[col].append(_type(row[col]))

    n_rows = len(products["product_code"])
    assert all(len(products[col]) == n_rows for col in products)  # check that all columns have all the rows.

    # Check that all columns have the same unit and that the source are either reported or ciqual.
    for nutient in used_nutrients:
        unique_units = set(products[nutient + "_unit"])
        assert len(unique_units) == 1, (nutient, unique_units)
        unique_sources = set(products[nutient + "_source"])
        assert unique_sources.issubset({"reported", "ciqual"}), (nutient, unique_sources)

    return products


def fix_prices(prices: dict[str, list[str | float]]):
    """Set all prices to the same currency: CHF. Also removes duplicate prices of the same location."""
    EUR_TO_CHF = 0.96  # TODO: fetch this from the internet.
    assert all(c in POSSIBLE_CURRENCIES for c in set(prices["currency"])), set(prices["currency"])
    prices["price_chf"] = [v * EUR_TO_CHF if c == "EUR" else v for v, c in zip(prices["price"], prices["currency"], strict=True)]  # type: ignore
    prices["price_eur"] = [v / EUR_TO_CHF if c == "CHF" else v for v, c in zip(prices["price"], prices["currency"], strict=True)]  # type: ignore


def get_arrays(
    bounds: dict[str, list[float]], products_and_prices: dict[str, list[str | float]], currency: str
) -> tuple[np.ndarray, ...]:
    # Check that the upper and lower bounds nutrients use the same units as the product nutrients.
    # for nutrient in bounds:
    #     product_unique_units = set(products_and_prices[nutrient + "_unit"])
    #     recommendation_unit = bounds[nutrient]["unit"]
    #     assert product_unique_units == {recommendation_unit}, (nutrient, product_unique_units, recommendation_unit)

    # Nutrients of each product
    A_nutrients = np.array([products_and_prices[nutrient + "_value"] for nutrient in bounds], dtype=np.float32)

    # Costs of each product (* 0.1 to go from price per kg to price per 100g)
    c_costs = 0.1 * np.array(products_and_prices[f"price_{currency.lower()}"], dtype=np.float32)

    # Bounds for nutrients
    b = np.array([bounds[nutrient] for nutrient in bounds], dtype=np.float32)
    lb, ub = b[:, 0], b[:, 1]

    return A_nutrients, lb, ub, c_costs


def solve_optimization(A, lb, ub, c):
    # Constraints for lower bounds
    A_ub_lb = -A[~np.isnan(lb)]
    b_ub_lb = -lb[~np.isnan(lb)]

    # Constraints for upper bounds
    A_ub_ub = A[~np.isnan(ub)]
    b_ub_ub = ub[~np.isnan(ub)]

    # Concatenate both constraints
    A_ub = np.vstack([A_ub_lb, A_ub_ub])
    b_ub = np.concatenate([b_ub_lb, b_ub_ub])

    # Solve the problem and result the result.
    return linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None))


def create_rangeslider(data: dict[str, str]) -> dict[str, float | str]:
    """Create the rangeslider of the given nutrient with the given data."""
    value_key = "value_males"  # "value_females"  # NOTE: using male values
    lower = float(data[value_key])
    upper = float(data["value_upper_intake"]) if data["value_upper_intake"] != "" else None
    _min = 0 if data["off_id"] != "energy-kcal" else 1000
    _max = 4 * lower if upper is None else math.ceil(upper + lower - _min)
    _max = _min + 100 if _max == _min else _max
    unit = data["unit"]
    # marks = {
    #     _min: {"label": f"{_min}{unit}"},
    #     _max: {"label": f"{_max}{unit}"},
    # }
    # if micro:
    #     marks[lower] = {"label": f"{lower}{unit}", "style": {"color": "#369c36"}}  # type: ignore
    # if micro and upper is not None:
    #     marks[upper] = {"label": f"{upper}{unit}", "style": {"color": "#f53d3d"}}  # type: ignore
    return {
        "name": data["ciqual_name"],
        "id": data["off_id"],
        "unit": unit,
        "min": _min,
        "max": _max,
        "lower": lower,
        "upper": upper if upper is not None else _max,
        # "tooltip": {"placement": "bottom", "always_visible": False, "template": f"{{value}}{unit}"},
        # "marks": marks,
    }


def filter_nutrients(nutrient_map: list[dict[str, str]], recommendations: list[dict[str, str]]) -> list[dict[str, str]]:
    available = {rec["off_id"] for rec in recommendations}
    return [{"name": row["ciqual_name"], "id": row["off_id"]} for row in nutrient_map if row["off_id"] in available]


def create_app(
    macro_recommendations: list[dict[str, str]],
    micro_recommendations: list[dict[str, str]],
    products_and_prices: dict[str, list[str | float]],
    nutrient_map: list[dict[str, str]],
) -> Flask:
    app = Flask(__name__)

    macronutrients = filter_nutrients(nutrient_map, macro_recommendations)
    micronutrients = filter_nutrients(nutrient_map, micro_recommendations)

    @app.route("/")
    def index():
        nutient_groups = [
            {"name": "Macronutrients", "id": "macro", "nutrients": macronutrients},
            {"name": "Micronutrients", "id": "micro", "nutrients": micronutrients},
        ]
        sliders = [create_rangeslider(rec) for rec in [*macro_recommendations, *micro_recommendations]]
        return render_template(
            "index.html",
            currencies=POSSIBLE_CURRENCIES,
            sliders=sliders,
            nutient_groups=nutient_groups,
        )

    @app.route("/optimize", methods=["POST"])
    def optimize():
        data = request.get_json()
        if DEBUG:
            return render_template("debug.html", data=data)

        currency = data["currency"]
        chosen_nutrient_ids = data["macro"] + data["micro"]

        # Remove previous level markers
        chosen_bounds = {}
        for nutrient_id in chosen_nutrient_ids:
            chosen_bounds[nutrient_id] = data[f"bounds_{nutrient_id}"]

        A_nutrients, lb, ub, c_costs = get_arrays(chosen_bounds, products_and_prices, currency)
        result = solve_optimization(A_nutrients, lb, ub, c_costs)
        if result.status != 0:
            return "<h1>No solution</h1>"

        # Calculate nutrient levels
        # nutrients_levels = A_nutrients @ result.x  # TODO: use nutrient levels.

        # Prepare data for rendering in the HTML table
        products = []
        for i in range(len(products_and_prices["product_code"])):
            product = {
                "product_code": products_and_prices["product_code"][i],
                "product_name": products_and_prices["product_name"][i],
                "ciqual_name": products_and_prices["ciqual_name"][i],
                "ciqual_code": products_and_prices["ciqual_code"][i],
                "location": products_and_prices["location"][i],
                "location_osm_id": products_and_prices["location_osm_id"][i],
                "quantity_g": round(100 * result.x[i], 1),
                "price": round(c_costs[i] * result.x[i], 2),
            }
            if product["quantity_g"] > 0:  # Filter out products with zero quantity
                products.append(product)

        return render_template("result.html", products=products, result=result, currency=currency)

    return app


if __name__ == "__main__":
    assert OFF_USERNAME is not None, f"Set OFF_USERNAME env variable {OFF_USERNAME=}"

    with (DATA_DIR / "nutrient_map.csv").open("r") as file:
        nutrient_map = [row_dict for row_dict in csv.DictReader(file) if not row_dict["disabled"]]

    with (DATA_DIR / "user_data" / OFF_USERNAME / "product_prices_and_nutrients.csv").open("r") as file:
        products_and_prices = load_and_filter_products(file, used_nutrients=[row_dict["off_id"] for row_dict in nutrient_map])
    fix_prices(products_and_prices)

    with (DATA_DIR / "recommendations_macro.csv").open("r") as file:
        macro_recommendations = inner_merge(list(csv.DictReader(file)), nutrient_map, left_key="off_id", right_key="off_id")

    with (DATA_DIR / "recommendations_nnr2023.csv").open("r") as file:
        micro_recommendations = inner_merge(list(csv.DictReader(file)), nutrient_map, left_key="nutrient", right_key="nnr2023_id")

    app = create_app(macro_recommendations, micro_recommendations, products_and_prices, nutrient_map)
    app.run(debug=True)
