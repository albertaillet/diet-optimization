#!/usr/bin/env -S uv run
"""This script creates a flask app for optimizing a diet with linear optimization to get the optimal quantities of food products.

TODO: Advanced filter: location, vegan, vegetarian, indiviudal off categories
TODO: Include other objectives with tunable hyperparameters (t.ex. minimize environmental impact, added sugar, saturated fat).
TODO: In frontend button to download the results as a CSV file.
TODO: Log all requests and responses in a database.
TODO: Benchmark different LP solvers performance.
"""

import csv
import io
import json
import math
import os
import time
from pathlib import Path

import duckdb
import numpy as np
from flask import Flask, render_template, request
from flask_compress import Compress
from scipy.optimize import linprog

DEBUG_DIR = Path(__file__).parent.parent / "tmp"
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
OFF_USERNAME = os.getenv("OFF_USERNAME")
POSSIBLE_CURRENCIES = ["EUR", "CHF"]
TEMPLATE_FOLDER = Path(__file__).parent / "frontend/html"
QUERY = (Path(__file__).parent / "queries/query.sql").read_text()
LP_METHOD = "revised simplex"


def query(con: duckdb.DuckDBPyConnection, location_like: str) -> dict[str, np.ndarray]:
    return con.execute(QUERY, parameters={"location_like": location_like}).fetchnumpy()


def query_list_of_dicts(con: duckdb.DuckDBPyConnection, query: str, **kwargs) -> list[dict[str, str]]:
    ex = con.execute(query, parameters=kwargs)
    cols = [d[0] for d in ex.description]  # type: ignore
    return [{c: r for c, r in zip(cols, row, strict=True)} for row in ex.fetchall()]


def get_arrays(
    bounds: dict[str, tuple[float, float]], products_and_prices: dict[str, np.ndarray], currency: str
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
    return linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None), method=LP_METHOD)


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


def create_csv(
    x: np.ndarray,
    chosen_bounds: dict[str, tuple[float, float]],
    products_and_prices: dict[str, np.ndarray],
    c_costs: np.ndarray,
    nutrients_levels: np.ndarray,
) -> str:
    # Sort by quantity and remove those with zero quantity
    indices = np.argsort(x)[::-1]
    indices = indices[x[indices] > 0]

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
            "quantity_g": round(100 * x[i], 1),  # type: ignore
            "price": round(c_costs[i] * x[i], 2),  # type: ignore
            **{nutrient_id: nutrients_levels[j, i].round(4) for j, nutrient_id in enumerate(chosen_bounds)},
        }
        writer.writerow(product)
    output.seek(0)
    return output.read()


def create_app(con: duckdb.DuckDBPyConnection) -> Flask:
    app = Flask(__name__)
    Compress(app)
    app.template_folder = TEMPLATE_FOLDER

    nutrient_map = query_list_of_dicts(con, """SELECT * FROM data.nutrient_map WHERE disabled IS NULL""")
    macro_recommendations = query_list_of_dicts(con, """SELECT * FROM data.recommendations WHERE nutrient_type = 'macro'""")
    micro_recommendations = query_list_of_dicts(con, """SELECT * FROM data.recommendations WHERE nutrient_type = 'micro'""")
    nutrient_ids = [nutrient["id"] for nutrient in nutrient_map]

    @app.route("/")
    def index():
        nutrient_groups = [
            {"name": "Macronutrients", "id": "macro", "nutrients": macro_recommendations},
            {"name": "Micronutrients", "id": "micro", "nutrients": micro_recommendations},
        ]
        sliders = [create_rangeslider(rec) for rec in [*macro_recommendations, *micro_recommendations]]
        return render_template("dashboard.html", currencies=POSSIBLE_CURRENCIES, sliders=sliders, nutrient_groups=nutrient_groups)

    @app.route("/optimize.csv", methods=["POST"])
    def optimize():
        data = request.get_json()
        currency = data["currency"]
        debug_folder = DEBUG_DIR / f"optimize/{time.strftime('%Y-%m-%d-%H-%M-%S')}-{time.perf_counter_ns()}"
        debug_folder.mkdir(parents=True)
        with (debug_folder / "input.json").open("w+") as f:
            f.write(json.dumps(data, indent=2))
        chosen_bounds = {nid: tuple(data[nid]) for nid in nutrient_ids if nid in data}
        if not chosen_bounds:
            return ""

        start = time.perf_counter()
        products_and_prices = query(con, location_like="Toulouse")  # TODO: this should be a parameter
        query_time = time.perf_counter() - start

        start = time.perf_counter()
        A_nutrients, lb, ub, c_costs = get_arrays(chosen_bounds, products_and_prices, currency)
        array_time = time.perf_counter() - start

        if A_nutrients.size == 0:
            return ""

        start = time.perf_counter()
        result = solve_optimization(A_nutrients, lb, ub, c_costs)
        optimization_time = time.perf_counter() - start
        (debug_folder / "times.json").write_text(
            json.dumps(
                {
                    "query_time": query_time,
                    "array_time": array_time,
                    "optimization_time": optimization_time,
                    "num_products": A_nutrients.shape[1],
                    "num_nutrients": A_nutrients.shape[0],
                },
                indent=2,
            )
        )
        if result.status != 0:
            return ""

        # Calculate nutrient levels
        nutrients_levels = A_nutrients * result.x
        assert (nutrients_levels < -1e-7).sum() == 0, "Negative values in nutrients_levels."

        reslut_csv_string = create_csv(result.x, chosen_bounds, products_and_prices, c_costs, nutrients_levels)
        (debug_folder / "output.csv").write_text(reslut_csv_string)
        return app.response_class(reslut_csv_string, mimetype="text/csv")

    @app.route("/info/<price_id>", methods=["GET"])
    def info(price_id: str) -> str:
        row_dicts = query_list_of_dicts(con, """SELECT * FROM data.final_table WHERE price_id = $price_id""", price_id=price_id)
        if len(row_dicts) == 0:
            return "<h1>Not found</h1>"
        return render_template("info.html", item=row_dicts[0])

    # serve all static files TODO: do this in a better way
    @app.route("/static/<path:path>")
    def send_static(path):
        return app.send_static_file(path)

    def get_locations_within_bounds(lat_min, lat_max, lon_min, lon_max):
        # TODO: Fix this function to use the actual database query
        center_lat, center_lon = (lat_min + lat_max) / 2, (lon_min + lon_max) / 2
        return [{"lat": center_lat, "lon": center_lon, "name": "Center Point"}]

    @app.route("/<lat_min>/<lat_max>/<lon_min>/<lon_max>/locations.csv", methods=["GET"])
    def location(lat_min, lat_max, lon_min, lon_max):
        """Return a CSV of the locations within the given tile."""
        lat_min, lat_max, lon_min, lon_max = map(int, (lat_min, lat_max, lon_min, lon_max))
        locations = get_locations_within_bounds(lat_min, lat_max, lon_min, lon_max)

        output = io.StringIO()  # Create a CSV output from the retrieved locations.  TODO: create a function, this is done twice
        writer = csv.DictWriter(output, fieldnames=["lat", "lon", "name"])
        writer.writeheader()
        for loc in locations:
            writer.writerow(loc)

        # Return the CSV response with appropriate MIME type.
        output.seek(0)
        return app.response_class(output.getvalue(), mimetype="text/csv")

    return app


con = duckdb.connect(DATA_DIR / "data.db", read_only=True)
app = create_app(con)

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8000)
