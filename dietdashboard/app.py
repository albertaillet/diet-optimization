"""This script combines the different summarized csv files and creates a dashboard to interact
with linear optimization to get the optimal quantities of food products.

Usage of script DATA_DIR=<path to data directory> OFF_USERNAME=<yourusername> python app.py

TODO: have link to load info card for each of the chosen products.
TODO: User authentication and save optimization input.
TODO: Advanced filter: location, vegan, vegetarian, indiviudal off categories

Long term todos:
- Retrieve prices in SQL database.
- User authenticaiton.

TODO: Include other objectives than price minimization with tunable hyperparameters.
For example being able to minimize enivronmental impact, added sugar, staruated fat.
TODO: Choose to include maximum values even when they are not available in recommendations.
TODO: Include breakdown source of each nutrient (either in popup, other page or in generated pdf).
"""

import csv
import math
import operator
import os
from pathlib import Path
from time import perf_counter

import duckdb
import numpy as np
from flask import Flask, render_template, request
from scipy.optimize import linprog

from utils.table import inner_merge

DEBUG = os.getenv("DEBUG")
DATA_DIR = Path(os.getenv("DATA_DIR", ""))
OFF_USERNAME = os.getenv("OFF_USERNAME")
POSSIBLE_CURRENCIES = ["EUR", "CHF"]

# Connect in read_only mode
con = duckdb.connect(DATA_DIR / "data.db", read_only=True)


def generate_query(chosen_bounds: dict[str, list[float]]) -> str:
    # Create the part of the SELECT statement that lists each nutrient's value.
    nutrient_select = ", ".join([f"{nutrient_id}_value" for nutrient_id in chosen_bounds])
    # Create filter conditions to remove rows where any chosen nutrient value is NULL.
    nutrient_filters = " AND ".join([f"{nutrient_id}_value IS NOT NULL" for nutrient_id in chosen_bounds])

    # TODO: SQL injection security
    return f"""
    SELECT
    price_id,
    product_code,
    product_name,
    ciqual_code,
    ciqual_name,
    price_per_quantity,
    currency,
    price_location,
    price_location_osm_id,
    -- Convert price to CHF using EUR_TO_CHF = 0.96:
    CASE WHEN currency = 'EUR' THEN price_per_quantity * 0.96 ELSE price_per_quantity END AS price_chf,
    CASE WHEN currency = 'CHF' THEN price_per_quantity / 0.96 ELSE price_per_quantity END AS price_eur,
    {nutrient_select}
    FROM final_table
    WHERE currency IN ('EUR', 'CHF')
    AND price_per_quantity IS NOT NULL
    AND {nutrient_filters}
    -- AND price_owner = '{OFF_USERNAME}'
    AND product_quantity > 0
    """


def get_arrays(
    bounds: dict[str, list[float]], products_and_prices: dict[str, list[str | float]], currency: str
) -> tuple[np.ndarray, ...]:
    # Check that the upper and lower bounds nutrients use the same units as the product nutrients.
    # for nutrient in bounds:
    #     product_unique_units = set(products_and_prices[nutrient + "_unit"])
    #     recommendation_unit = bounds[nutrient]["unit"]
    #     assert product_unique_units == {recommendation_unit}, (nutrient, product_unique_units, recommendation_unit)
    # TODO: concatentation could be used for A and c is already a numpy array.

    # Nutrients of each product
    A_nutrients = np.array([products_and_prices[nutrient_id + "_value"] for nutrient_id in bounds], dtype=np.float32)

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
    _min = 0
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
        "id": data["id"],
        "unit": unit,
        "min": _min,
        "max": _max,
        "lower": lower,
        "upper": upper if upper is not None else _max,
        # "tooltip": {"placement": "bottom", "always_visible": False, "template": f"{{value}}{unit}"},
        # "marks": marks,
    }


def filter_nutrients(nutrient_map: list[dict[str, str]], recommendations: list[dict[str, str]]) -> list[dict[str, str]]:
    available = {rec["id"] for rec in recommendations}
    return [{"name": row["ciqual_name"], "id": row["id"]} for row in nutrient_map if row["id"] in available]


def create_app(
    macro_recommendations: list[dict[str, str]],
    micro_recommendations: list[dict[str, str]],
    nutrient_map: list[dict[str, str]],
) -> Flask:
    app = Flask(__name__)

    nutrient_ids = [nutrient["id"] for nutrient in nutrient_map]

    macronutrients = filter_nutrients(nutrient_map, macro_recommendations)
    micronutrients = filter_nutrients(nutrient_map, micro_recommendations)

    @app.route("/")
    def index():
        nutrient_groups = [
            {"name": "Macronutrients", "id": "macro", "nutrients": macronutrients},
            {"name": "Micronutrients", "id": "micro", "nutrients": micronutrients},
        ]
        sliders = [create_rangeslider(rec) for rec in [*macro_recommendations, *micro_recommendations]]
        return render_template(
            "index.html",
            currencies=POSSIBLE_CURRENCIES,
            sliders=sliders,
            nutrient_groups=nutrient_groups,
        )

    @app.route("/optimize", methods=["POST"])
    def optimize():
        data = request.get_json()
        if DEBUG:
            return render_template("debug.html", data=data)

        currency = data["currency"]

        # Remove previous level markers
        chosen_bounds = {}
        for nutrient_id in nutrient_ids:
            if data.get(f"bounds_{nutrient_id}") is None:
                continue
            chosen_bounds[nutrient_id] = data[f"bounds_{nutrient_id}"]

        # Time the query
        start = perf_counter()
        products_and_prices = con.execute(generate_query(chosen_bounds)).fetchnumpy()
        print(f"Query time: {perf_counter() - start:.2f}s")

        start = perf_counter()
        A_nutrients, lb, ub, c_costs = get_arrays(chosen_bounds, products_and_prices, currency)
        print(f"Array conversion time: {perf_counter() - start:.2f}s")

        print(f"Number of products: {A_nutrients.shape[1]}")
        print(f"Number of nutrients: {A_nutrients.shape[0]}")

        start = perf_counter()
        result = solve_optimization(A_nutrients, lb, ub, c_costs)
        print(f"Optimization time: {perf_counter() - start:.2f}s")
        if result.status != 0:
            return "<h1>No solution</h1>"

        n_products = A_nutrients.shape[1]

        # Calculate nutrient levels
        nutrients_levels = A_nutrients * result.x  # TODO: use nutrient levels.
        assert (nutrients_levels < 0).sum() == 0, "Negative values in nutrients_levels."

        # Prepare data for rendering in the HTML table
        products = []
        for i in range(n_products):
            if result.x[i] <= 0:  # Filter out products with zero quantity
                continue
            location = ", ".join(str(products_and_prices["price_location"][i]).split(", ")[:3])

            product = {
                "price_id": int(products_and_prices["price_id"][i]),
                "product_code": products_and_prices["product_code"][i],
                "product_name": products_and_prices["product_name"][i],
                "ciqual_name": products_and_prices["ciqual_name"][i],
                "ciqual_code": products_and_prices["ciqual_code"][i],
                "location": location,
                "location_osm_id": products_and_prices["price_location_osm_id"][i],
                "quantity_g": round(100 * result.x[i], 1),
                "price": round(c_costs[i] * result.x[i], 2),
                "levels": {nutrient_id: nutrients_levels[j, i] for j, nutrient_id in enumerate(chosen_bounds)},
            }
            products.append(product)

        products = sorted(products, key=operator.itemgetter("quantity_g"), reverse=True)

        nutrients = {}
        for p in products:
            for nutrient_id, level in p["levels"].items():
                if nutrient_id not in nutrients:
                    nutrients[nutrient_id] = []
                if level == 0:
                    continue
                nutrients[nutrient_id].append({"name": p["ciqual_name"], "id": p["price_id"], "level": level})

        product_indices = {p["price_id"]: i for i, p in enumerate(products)}
        return render_template(
            "result.html",
            products=products,
            result=result,
            currency=currency,
            nutrients=nutrients,
            product_indices=product_indices,
        )

    return app


if __name__ == "__main__":
    with (DATA_DIR / "nutrient_map.csv").open("r") as file:
        nutrient_map = [row_dict for row_dict in csv.DictReader(file) if not row_dict["disabled"]]

    with (DATA_DIR / "recommendations_macro.csv").open("r") as file:
        macro_recommendations = inner_merge(list(csv.DictReader(file)), nutrient_map, left_key="id", right_key="id")

    with (DATA_DIR / "recommendations_nnr2023.csv").open("r") as file:
        micro_recommendations = inner_merge(list(csv.DictReader(file)), nutrient_map, left_key="nutrient", right_key="nnr2023_id")

    app = create_app(macro_recommendations, micro_recommendations, nutrient_map)
    app.run(debug=True, host="localhost", port=5001)
