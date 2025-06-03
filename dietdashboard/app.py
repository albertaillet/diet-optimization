#!/usr/bin/env -S uv run
"""This script creates a flask app for optimizing a diet with linear optimization to get the optimal quantities of food products.

TODO: Advanced filter: vegan, vegetarian, indiviudal off categories
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
from collections.abc import Iterable
from pathlib import Path

import duckdb
import numpy as np
from flask import Flask, make_response, render_template, request
from flask_compress import Compress
from scipy.optimize import linprog

DEBUG_DIR = Path(__file__).parent.parent / "tmp"
DATA_DIR = Path(__file__).parent.parent / "data"
OFF_USERNAME = os.getenv("OFF_USERNAME")
POSSIBLE_CURRENCIES = ["EUR", "CHF"]
TEMPLATE_FOLDER = Path(__file__).parent / "frontend/html"
QUERY = (Path(__file__).parent / "queries/query.sql").read_text()
LP_METHOD = "revised simplex"
CACHE_TIMEOUT = 60 * 10  # 10 minutes


def query_numpy(con: duckdb.DuckDBPyConnection, query: str, **kwargs) -> dict[str, np.ndarray]:
    return con.execute(query, parameters=kwargs).fetchnumpy()


def query_dicts(con: duckdb.DuckDBPyConnection, query: str, **kwargs) -> list[dict[str, str]]:
    con.execute(query, parameters=kwargs)
    cols = [d[0] for d in con.description or []]
    return [{c: r for c, r in zip(cols, row, strict=True)} for row in con.fetchall()]


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
        "min": min_value,
        "max": max_value,
        "lower": lower,
        "upper": upper if upper is not None else max_value,
        "active": 1,
    }


def create_csv(fieldnames: list[str], data: Iterable[dict[str, str]]) -> str:
    """Convert a list of dictionaries to a CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["COMPRESS_MIMETYPES"] = ["text/html", "text/css", "text/javascript", "text/csv", "text/plain"]
    Compress(app)
    app.template_folder = TEMPLATE_FOLDER

    con = duckdb.connect(DATA_DIR / "data.db", read_only=True)

    recommendations = query_dicts(con, """SELECT * FROM recommendations""")
    nutrient_ids = [row["id"] for row in recommendations]
    sliders = [{k: rec[k] for k in ("id", "name", "unit", "nutrient_type")} | create_rangeslider(rec) for rec in recommendations]
    slider_csv = create_csv(["id", "name", "unit", "nutrient_type", "min", "max", "lower", "upper", "active"], sliders)  # type: ignore[reportArgumentType]

    @app.route("/")
    def index():
        return render_template("dashboard.html", slider_csv=slider_csv, currencies=POSSIBLE_CURRENCIES)

    @app.route("/optimize.csv", methods=["POST"])
    def optimize():
        data = request.get_json()
        currency = data["currency"]
        debug_folder = DEBUG_DIR / f"optimize/{time.strftime('%Y-%m-%d-%H-%M-%S')}-{time.perf_counter_ns()}"
        debug_folder.mkdir(parents=True)
        with (debug_folder / "input.json").open("w+") as f:
            f.write(json.dumps(data, indent=2))
        chosen_bounds = {nid: (data.get(f"{nid}_lower"), data.get(f"{nid}_upper")) for nid in nutrient_ids}
        locations = [int(loc) for loc in data.get("locations", [154])]  # id: 154, name: Auchan, Rue Lieutenant André Argenton
        if not chosen_bounds:
            print("No nutrients selected.")
            return ""

        start = time.perf_counter()
        products_and_prices = query_numpy(con, QUERY, locations=locations)
        query_time = time.perf_counter() - start

        start = time.perf_counter()
        A_nutrients, lb, ub, c_costs = get_arrays(chosen_bounds, products_and_prices, currency)
        array_time = time.perf_counter() - start

        if A_nutrients.size == 0:
            print("No products found.")
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
            print(f"Optimization failed: {result.message}")
            return ""

        # Calculate nutrient levels
        nutrients_levels = A_nutrients * result.x
        assert (nutrients_levels < -1e-7).sum() == 0, "Negative values in nutrients_levels."

        x = result.x
        # Sort by quantity and remove those with zero quantity
        indices = np.argsort(x)[::-1]
        indices = indices[x[indices] > 1e-3]

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
            *list(chosen_bounds),
        ]
        optimal_products = []
        for i in indices:
            location = ", ".join(str(products_and_prices["location_osm_display_name"][i]).split(", ")[:3])
            product = {
                "id": int(products_and_prices["price_id"][i]),
                "product_code": products_and_prices["product_code"][i],
                "product_name": products_and_prices["product_name"][i],
                "ciqual_name": products_and_prices["ciqual_name"][i],
                "ciqual_code": products_and_prices["ciqual_code"][i],
                "location": location,
                "location_osm_id": products_and_prices["location_osm_id"][i],
                "quantity_g": round(100 * x[i], 1),  # type: ignore
                "price": round(c_costs[i] * x[i], 2),  # type: ignore
                **{nutrient_id: nutrients_levels[j, i].round(4) for j, nutrient_id in enumerate(chosen_bounds)},
            }
            optimal_products.append(product)
        reslut_csv_string = create_csv(fieldnames, optimal_products)
        (debug_folder / "output.csv").write_text(reslut_csv_string)  # Write the CSV to the debug folder
        response = make_response(reslut_csv_string)
        response.mimetype = "text/csv"
        return response

    @app.route("/info/<price_id>", methods=["GET"])
    def info(price_id: str) -> str:
        row_dicts = query_dicts(con, """SELECT * FROM data.final_table WHERE price_id = $price_id""", price_id=price_id)
        if len(row_dicts) == 0:
            return "<h1>Not found</h1>"
        return render_template("info.html", item=row_dicts[0])

    # serve all static files TODO: do this in a better way
    @app.route("/static/<path:path>")
    def send_static(path):
        return app.send_static_file(path)

    @app.route("/locations.csv", methods=["GET"])
    def locations():
        """Return a CSV of the locations within the given tile."""
        con = duckdb.connect(DATA_DIR / "data.db", read_only=True)
        query = """SELECT DISTINCT ON (location_id)
            location_id, location_osm_lat, location_osm_lon, location_osm_display_name, COUNT(*) AS count
            FROM final_table
            GROUP BY location_id, location_osm_lat, location_osm_lon, location_osm_display_name"""
        locations = query_dicts(con=con, query=query)
        fieldnames = ["id", "lat", "lon", "name", "count"]
        colnames = ["location_id", "location_osm_lat", "location_osm_lon", "location_osm_display_name", "count"]
        data = ({f: loc[c] for f, c in zip(fieldnames, colnames, strict=True)} for loc in locations)
        csv_string = create_csv(fieldnames, data)
        response = make_response(csv_string)
        response.mimetype = "text/csv"
        response.headers["Cache-Control"] = f"public, max-age={CACHE_TIMEOUT}"
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="localhost", port=8000)
