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
import re
import time
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import unquote

import duckdb
import numpy as np
from flask import Flask, make_response, render_template, request
from flask_compress import Compress
from scipy.optimize import linprog

from dietdashboard.objective import validate_objective_str

DEBUG_DIR = Path(__file__).parent.parent / "tmp"
DATA_DIR = Path(__file__).parent.parent / "data"
TEMPLATE_FOLDER = Path(__file__).parent / "frontend/html"
STATIC_FOLDER = Path(__file__).parent / "static"
QUERY = (Path(__file__).parent.parent / "queries/query.sql").read_text()
LP_METHOD = "revised simplex"
CACHE_TIMEOUT = 60 * 10  # 10 minutes
SQL_ERROR_COL_REF_REGEX = re.compile(r"Binder Error: Referenced column \"([a-zA-Z_]+)\" not found in FROM clause!")
ACTIVE_THRESHOLD = 1e-3  # Threshold to consider a constraint as active
PRODUCT_THRESHOLD = 1e-3  # Minimum quantity in grams to include a product in the output


def get_con() -> duckdb.DuckDBPyConnection:
    """Get a connection to the DuckDB database."""
    return duckdb.connect(DATA_DIR / "data.db", read_only=True)


def validate_objective(con: duckdb.DuckDBPyConnection, objective_string: str) -> tuple[bool, str]:
    """Validate the objective function expression."""
    valid, _ = validate_objective_str(objective_string)
    if not valid:
        return False, "Invalid objective function syntax."
    try:
        # Checks that the column exists and that it is a numeric (https://duckdb.org/docs/stable/sql/data_types/numeric.html)
        out = con.sql(f"""SELECT column_name FROM (DESCRIBE (SELECT {objective_string} from final_table_price))
                    WHERE column_type NOT IN ('DECIMAL', 'FLOAT', 'DOUBLE', 'REAL');""").fetchone()
        if out:
            return False, f"Variable {out[0]} is not numeric."
    except duckdb.BinderException as e:
        if match := SQL_ERROR_COL_REF_REGEX.match(str(e)):
            return False, f"Variable '{match.group(1)}' not found."
        return False, "SQL error"
    return valid, "Valid objective function."


def query_numpy(con: duckdb.DuckDBPyConnection, query: str, **kwargs) -> dict[str, np.ndarray]:
    return con.execute(query, parameters=kwargs).fetchnumpy()


def query_dicts(con: duckdb.DuckDBPyConnection, query: str, **kwargs) -> list[dict[str, str]]:
    con.execute(query, parameters=kwargs)
    cols = [d[0] for d in con.description or []]
    return [{c: r for c, r in zip(cols, row, strict=True)} for row in con.fetchall()]


def get_arrays(bounds: dict[str, tuple[float, float]], products_and_prices: dict[str, np.ndarray]) -> tuple[np.ndarray, ...]:
    # Nutrients of each product
    A_nutrients = np.array([products_and_prices[nutrient_id] for nutrient_id in bounds], dtype=np.float32)

    # Costs of each product
    c_costs = np.array(products_and_prices["objective"], dtype=np.float32)

    # Bounds for nutrients
    b = np.array([bounds[nutrient] for nutrient in bounds], dtype=np.float32)
    lb, ub = b[:, 0], b[:, 1]

    return A_nutrients, lb, ub, c_costs


def solve_optimization(A, lb, ub, c):
    # Concatenate contraints for lower bounds the upper bounds.
    A_ub = np.vstack([-A, A])
    b_ub = np.concatenate([-lb, ub])
    return linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None), method=LP_METHOD)


def create_rangeslider(data: dict[str, str]) -> dict[str, float | str]:
    """Create the rangeslider of the given nutrient with the given data."""
    value_key = "value_males"  # "value_females"  # NOTE: using male values
    lower = float(data[value_key])
    upper = float(data["value_upper_intake"]) if data["value_upper_intake"] is not None else None
    min_value = 0
    max_value = 4 * lower if upper is None else math.ceil(upper + lower - min_value)
    max_value = min_value + 100 if max_value == min_value else max_value
    return {"min": min_value, "max": max_value, "lower": lower, "upper": upper if upper is not None else max_value, "active": 1}


def create_csv(fieldnames: list[str], data: Iterable[dict[str, str]]) -> str:
    """Convert a list of dictionaries to a CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def create_app() -> Flask:
    # TODO: serve static files with Caddy
    app = Flask(__name__, static_folder=STATIC_FOLDER, template_folder=TEMPLATE_FOLDER)
    app.config["COMPRESS_MIMETYPES"] = ["text/html", "text/css", "text/javascript", "text/csv", "text/plain"]
    Compress(app)
    con = get_con()

    # Create sliders
    recommendations = query_dicts(con=con, query="""SELECT * FROM recommendations""")
    nutrient_ids = [row["id"] for row in recommendations]
    sliders = [{k: rec[k] for k in ("id", "name", "unit", "nutrient_type")} | create_rangeslider(rec) for rec in recommendations]
    slider_csv = create_csv(["id", "name", "unit", "nutrient_type", "min", "max", "lower", "upper", "active"], sliders)  # type: ignore[reportArgumentType]

    # Create nutrient for info page (and order them)
    q = """SELECT nutrient_type, list({'id': id, 'name': name, 'unit': ciqual_unit}) AS nutrients
             FROM nutrient_map GROUP BY nutrient_type"""
    grouped_nutrients = query_dicts(con=con, query=q)
    order = {nt: i for i, nt in enumerate(["energy", "macro", "sugar", "fatty_acid", "mineral", "vitamin", "other"])}
    grouped_nutrients.sort(key=lambda x: order.get(x["nutrient_type"], len(order)))

    con.close()

    @app.route("/")
    def index():
        return render_template("dashboard.html", slider_csv=slider_csv)

    @app.route("/validate_objective", methods=["GET"])
    def validate():
        """Validate the objective function expression."""
        objective_string = request.args.get("q", "")
        with get_con() as con:
            valid, message = validate_objective(con, unquote(objective_string))  # unquote to decode URL-encoded characters
        return app.json.response({"valid": valid, "message": message})

    @app.route("/optimize.csv", methods=["POST"])
    def optimize():
        data = request.get_json()
        objective = data["objective"]
        con = get_con()
        valid, message = validate_objective(con, objective)
        if not valid:
            return f"Invalid objective function: {message}"
        debug_folder = DEBUG_DIR / f"optimize/{time.strftime('%Y-%m-%d-%H-%M-%S')}-{time.perf_counter_ns()}"
        debug_folder.mkdir(parents=True)
        with (debug_folder / "input.json").open("w+") as f:
            f.write(json.dumps(data, indent=2))
        chosen_bounds = {
            nid: (data.get(f"{nid}_lower"), data.get(f"{nid}_upper"))
            for nid in nutrient_ids
            if f"{nid}_lower" in data and f"{nid}_upper" in data
        }
        if not chosen_bounds:
            return "No nutrients selected."
        locations = [int(loc) for loc in data["locations"]]  # id: 154, name: Auchan, Rue Lieutenant André Argenton
        if not locations:
            return "No locations selected."

        start = time.perf_counter()
        q = QUERY.replace("$objective", objective)  # Replace the placeholder with the actual objective function
        chosen_nutrient_ids = [nid for nid in nutrient_ids if nid in chosen_bounds]
        num_nutrients = len(chosen_nutrient_ids)
        products_and_prices = query_numpy(con, q, locations=locations, nutrient_ids=chosen_nutrient_ids)
        query_time = time.perf_counter() - start
        con.close()

        start = time.perf_counter()
        A_nutrients, lb, ub, c_costs = get_arrays(chosen_bounds, products_and_prices)
        array_time = time.perf_counter() - start

        if A_nutrients.size == 0:
            return "No products found."

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
                    "num_nutrients": num_nutrients,
                },
                indent=2,
            )
        )
        if result.status != 0:
            return f"Optimization failed: {result.message}"

        # Calculate nutrient levels
        nutrients_levels = A_nutrients * result.x
        assert (nutrients_levels < -1e-7).sum() == 0, "Negative values in nutrients_levels."

        # Determine which constraints are active, when slack is close to 0, the constraint is active
        # assert len(result.slack) == 2 * len(chosen_bounds)
        active_constraints = [
            {"nutrient_id": chosen_nutrient_ids[i % num_nutrients]}
            for i, slack in enumerate(result.slack)
            if abs(slack) <= ACTIVE_THRESHOLD
        ]

        x = result.x
        # Sort by quantity and remove those with zero quantity
        indices = np.argsort(x)[::-1]
        indices = indices[x[indices] > PRODUCT_THRESHOLD]

        fieldnames = [
            "id",
            "product_code",
            "product_name",
            "ciqual_name",
            "ciqual_code",
            "color",
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
                "color": products_and_prices["color"][i],
                "location": location,
                "location_osm_id": products_and_prices["location_osm_id"][i],
                "quantity_g": round(100 * x[i], 1),
                "price": round(products_and_prices["price"][i] * x[i], 2),
                **{nutrient_id: nutrients_levels[j, i].round(4) for j, nutrient_id in enumerate(chosen_bounds)},
            }
            optimal_products.append(product)
        result_csv_string = create_csv(fieldnames, optimal_products)
        (debug_folder / "output.csv").write_text(result_csv_string)  # Write the CSV to the debug folder
        response = make_response(result_csv_string)
        response.mimetype = "text/csv"
        response.headers["Binding-Constraints"] = json.dumps(active_constraints)
        return response

    @app.route("/info/<price_id>", methods=["GET"])
    def info(price_id: str) -> str:
        with get_con() as con:
            rows = query_dicts(con, """SELECT * FROM final_table_price WHERE price_id = $price_id""", price_id=price_id)
        if len(rows) == 0:
            return "<h1>No product found</h1>"
        row = rows[0]
        return render_template("info.html", item=row, grouped_nutrients=grouped_nutrients)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=8000)
