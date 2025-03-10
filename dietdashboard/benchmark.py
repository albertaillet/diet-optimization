#!/usr/bin/env -S uv run
"""This script benchmarks differency methods for running linear programming"""

import json
import time
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

DATA_DIR = Path("data")
BENCHMARK_DATA = DATA_DIR / "benchmark.npz"


# def save_benchmark_data():
#     import duckdb
#     QUERY = (Path(__file__).parent / "queries/query.sql").read_text()
#     con = duckdb.connect(DATA_DIR / "data.db", read_only=True)
#     out = con.execute(QUERY, parameters={"location_like": "Grenoble"}).fetchnumpy()
#     np.savez_compressed(BENCHMARK_DATA, **out)
#     recommendations = query_list_of_dicts(con, """SELECT * FROM data.recommendations""")
#     bounds = {row["id"]: (float(row["value_males"]), row["value_upper_intake"]) for row in recommendations}


def get_arrays(
    bounds: dict[str, tuple[float, float | None]], products_and_prices: dict[str, np.ndarray]
) -> tuple[np.ndarray, ...]:
    # Nutrients of each product
    A_nutrients = np.array([products_and_prices[nutrient_id + "_value"] for nutrient_id in bounds], dtype=np.float32)

    # Costs of each product (* 0.1 to go from price per kg to price per 100g)
    c_costs = 0.1 * np.array(products_and_prices["price_eur"], dtype=np.float32)

    # Bounds for nutrients
    b = np.array([bounds[nutrient] for nutrient in bounds], dtype=np.float32)
    lb, ub = b[:, 0], b[:, 1]

    return A_nutrients, lb, ub, c_costs


def solve_optimization_scipy(A, lb, ub, c, method):
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
    # callbacks = {"callback": linprog_terse_callback} if "high" not in method else {}
    return linprog(
        c,
        A_ub=A_ub,
        b_ub=b_ub,
        bounds=(0, None),
        method=method,
        options={"disp": False, "presolve": False, "maxiter": 10_000},
        integrality=0,
    )


if __name__ == "__main__":
    # save_benchmark_data()
    bounds = json.load((DATA_DIR / "input.json").open())
    products_and_prices = np.load(BENCHMARK_DATA)

    A_nutrients, lb, ub, c_costs = get_arrays(bounds, products_and_prices)  # type: ignore

    print(A_nutrients.shape, lb.shape, ub.shape, c_costs.shape)

    results = {}
    for limit in [100, 1000, 2000]:
        results[limit] = {}
        fun = -1
        for method in ["highs", "highs-ds", "highs-ipm", "interior-point", "revised simplex", "simplex"]:
            A = A_nutrients[:, :limit]
            c = c_costs[:limit]
            start = time.perf_counter()
            out = solve_optimization_scipy(A, lb, ub, c, method)
            optimization_time = time.perf_counter() - start
            results[limit][method] = optimization_time
            assert out.success, (method, limit, out)
            if fun == -1:
                fun = out.fun
            elif fun is not None and abs(fun - out.fun) > 1e-3:
                print("different result", method, fun, limit, out.fun)

    print(json.dumps(results, indent=2))
