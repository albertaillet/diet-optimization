#!/usr/bin/env -S uv run
"""This script creates a flask app for optimizing a diet with linear optimization to get the optimal quantities of food products.

TODO: Advanced filter: location, vegan, vegetarian, indiviudal off categories
TODO: Include other objectives with tunable hyperparameters (t.ex. minimize environmental impact, added sugar, saturated fat).
TODO: In frontend possibility to change max and min value of sliders.
TODO: In frontend button to download the results as a CSV file.
TODO: Log all requests and responses in a database.
TODO: Combine both macro and micro nutrient_groups in the same dropdown.
TODO: Benchmark different LP solvers performance.
"""

import csv
import io
import json
import math
import os
from pathlib import Path
from time import perf_counter

import duckdb
import numpy as np
from flask import Flask, render_template, request
from scipy.optimize import linprog

DEBUG = os.getenv("DEBUG")
DEBUG_DIR = Path(__file__).parent.parent / "tmp"
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
OFF_USERNAME = os.getenv("OFF_USERNAME")
POSSIBLE_CURRENCIES = ["EUR", "CHF"]
QUERY = (Path(__file__).parent / "queries/query.sql").read_text()


def query(con: duckdb.DuckDBPyConnection, location_like: str) -> dict[str, np.ndarray]:
    return con.execute(QUERY, parameters={"location_like": location_like}).fetchnumpy()


def query_list_of_dicts(con: duckdb.DuckDBPyConnection, query: str, **kwargs) -> list[dict[str, str]]:
    ex = con.execute(query, parameters=kwargs)
    cols = [d[0] for d in ex.description]  # type: ignore
    return [{c: r for c, r in zip(cols, row, strict=True)} for row in ex.fetchall()]


def get_arrays(
    bounds: dict[str, list[float]], products_and_prices: dict[str, np.ndarray], currency: str
) -> tuple[np.ndarray, ...]:
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
    upper = float(data["value_upper_intake"]) if data["value_upper_intake"] is not None else None
    min_value = 0
    max_value = 4 * lower if upper is None else math.ceil(upper + lower - min_value)
    max_value = min_value + 100 if max_value == min_value else max_value
    return {
        "name": data["name"],
        "id": data["id"],
        "unit": data["rec_unit"],
        "min": min_value,
        "max": max_value,
        "lower": lower,
        "upper": upper if upper is not None else max_value,
    }


def create_app(
    con: duckdb.DuckDBPyConnection,
    macro_recommendations: list[dict[str, str]],
    micro_recommendations: list[dict[str, str]],
    nutrient_map: list[dict[str, str]],
) -> Flask:
    app = Flask(__name__)

    nutrient_ids = [nutrient["id"] for nutrient in nutrient_map]

    macronutrients = [row["id"] for row in macro_recommendations]
    micronutrients = [row["id"] for row in micro_recommendations]

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

    @app.route("/optimize.csv", methods=["POST"])
    def optimize():
        data = request.get_json()
        currency = data["currency"]
        if DEBUG:
            with (DEBUG_DIR / "input.json").open("w+") as f:
                f.write(json.dumps(data, indent=2))
        chosen_bounds = {}
        for nutrient_id in nutrient_ids:
            if nutrient_id not in data:
                continue
            chosen_bounds[nutrient_id] = data[nutrient_id]

        start = perf_counter()
        products_and_prices = query(con, location_like="Toulouse")  # TODO: this should be a parameter
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
            return ""

        # Calculate nutrient levels
        nutrients_levels = A_nutrients * result.x
        assert (nutrients_levels < 0).sum() == 0, "Negative values in nutrients_levels."

        # Sort by quantity and remove those with zero quantity
        indices = np.argsort(result.x)[::-1]
        indices = indices[result.x[indices] > 0]

        # Prepare data for rendering in the HTML table
        output = io.StringIO()
        fieldnames = [
            "id",
            "product_code",
            "product_name",
            "ciqual_name",
            "ciqual_code",
            "location",
            "location_osm_id",
            "quantity_g",
            "price",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames + list(chosen_bounds))
        writer.writeheader()
        for i in indices:
            location = ", ".join(str(products_and_prices["price_location"][i]).split(", ")[:3])
            product = {
                "id": int(products_and_prices["price_id"][i]),
                "product_code": products_and_prices["product_code"][i],
                "product_name": products_and_prices["product_name"][i],
                "ciqual_name": products_and_prices["ciqual_name"][i],
                "ciqual_code": products_and_prices["ciqual_code"][i],
                "location": location,
                "location_osm_id": products_and_prices["price_location_osm_id"][i],
                "quantity_g": round(100 * result.x[i], 1),
                "price": round(c_costs[i] * result.x[i], 2),
                **{nutrient_id: nutrients_levels[j, i].round(4) for j, nutrient_id in enumerate(chosen_bounds)},
            }
            writer.writerow(product)
        output.seek(0)
        if DEBUG:
            with (DEBUG_DIR / "output.csv").open("w+") as f:
                f.write(output.read())
            output.seek(0)
        return output.read()

    @app.route("/info/<price_id>", methods=["GET"])
    def info(price_id: str) -> str:
        row_dicts = query_list_of_dicts(con, "SELECT * FROM final_table WHERE price_id = $price_id", price_id=price_id)
        if len(row_dicts) == 0:
            return "<h1>Not found</h1>"
        return render_template("info.html", item=row_dicts[0])

    # serve all static files TODO: do this in a better way
    @app.route("/static/<path:path>")
    def send_static(path):
        return app.send_static_file(path)

    return app


con = duckdb.connect(DATA_DIR / "data.db", read_only=True)

nutrient_map = query_list_of_dicts(con, """SELECT * FROM nutrient_map WHERE disabled IS NULL""")
macro_recommendations = query_list_of_dicts(con, """SELECT * FROM recommendations WHERE nutrient_type = 'macro'""")
micro_recommendations = query_list_of_dicts(con, """SELECT * FROM recommendations WHERE nutrient_type = 'micro'""")

app = create_app(con, macro_recommendations, micro_recommendations, nutrient_map)

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8000)
