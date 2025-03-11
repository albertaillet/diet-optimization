#!/usr/bin/env -S uv run --extra benchmark
"""This script benchmarks differency methods for running linear programming"""

import json
import time
import warnings
from datetime import datetime
from pathlib import Path

import cvxpy as cp
import numpy as np
from scipy.optimize import linprog

DATA_DIR = Path("data")
BENCHMARK_DATA = DATA_DIR / "benchmark.npz"
BENCHMARK_RESULTS = DATA_DIR / "benchmark_results.json"

warnings.filterwarnings("ignore", category=DeprecationWarning)  # filter scipy DeprecationWarning

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
    options = {"disp": False, "presolve": False, "maxiter": 10_000, "autoscale": False}
    if "highs" in method:
        options.pop("autoscale")
    return linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None), method=method, options=options, integrality=0)


def solve_optimization_cvxpy(A, lb, ub, c, solver_path):
    x = cp.Variable(c.shape[0])
    objective = cp.Minimize(c @ x)
    constraints = [x >= 0, A[~np.isnan(lb)] @ x >= lb[~np.isnan(lb)], A[~np.isnan(ub)] @ x <= ub[~np.isnan(ub)]]
    prob = cp.Problem(objective, constraints)
    return prob.solve(solver_path=solver_path, verbose=False)


if __name__ == "__main__":
    # save_benchmark_data()
    bounds = json.load((DATA_DIR / "input.json").open())
    # bounds = {k: bounds[k] for k in ["energy_fibre_kcal", "protein", "carbohydrate", "fat"]}
    products_and_prices = np.load(BENCHMARK_DATA)
    A_nutrients, lb, ub, c_costs = get_arrays(bounds, products_and_prices)  # type: ignore
    solvers = {
        "cvxpy": [
            # ("CBC"),
            ("CLARABEL"),  # clarabel settings: clarabel.DefaultSettings
            ("CLARABEL", {"max_iter": 1000}),
            # ("COPT"),  # not sure how to install COPT
            # ("DAQP"),
            # ("GLOP"),
            ("GLPK"),
            ("GLPK_MI"),
            # ("OSQP"),
            # ("PIQP"),
            # ("PROXQP"),
            # ("PDLP"),
            # ("CPLEX"),
            # ("NAG"),
            # ("ECOS"),
            # ("GUROBI"),  # requires license
            ("MOSEK"),  # requires license
            ("CVXOPT"),  # no MIP
            # ("SDPA"),
            ("SCS"),
            # ("SCIP"),
            # ("XPRESS"),
            ("SCIPY", {"scipy_options": {"method": "highs"}}),
            ("SCIPY", {"scipy_options": {"method": "highs-ds"}}),
            ("SCIPY", {"scipy_options": {"method": "highs-ipm"}}),
            # ("SCIPY", {"scipy_options": {"method": "interior-point"}}),  # not working, since matrices are sparse in cvxpy
            # ("SCIPY", {"scipy_options": {"method": "revised simplex"}}),
            # ("SCIPY", {"scipy_options": {"method": "simplex"}}),
            # ("HiGHS"),
        ],
        "scipy": ["highs", "highs-ds", "highs-ipm", "interior-point", "revised simplex", "simplex"],
    }
    # Currently best:
    # GLPK_MI for MIP and speed
    # scipy interior-point for LP and speed

    results = {}
    limits = [60, 100, 1000, 2000]
    for limit in limits:  # , 1000, 2000]:  # , 10000]:
        results[limit] = {}
        saved_objective = -1
        A = A_nutrients[:, :limit]
        c = c_costs[:limit]
        for library in solvers:
            for method in solvers[library]:
                start = time.perf_counter()
                if library == "scipy":
                    out = solve_optimization_scipy(A, lb, ub, c, method)
                    # assert out == "optimal", (method, limit, out)
                    # assert out.success, (method, limit, out)
                    print(f"(scipy) {datetime.now().strftime('%b %d %I:%M:%S %p')}: Solver {method} succeeds")
                    objective = float(out.fun)
                elif library == "cvxpy":
                    out = solve_optimization_cvxpy(A, lb, ub, c, solver_path=[method])
                    objective = float(out)  # type: ignore
                    method = f"scipy-{method}"
                else:
                    raise ValueError(f"Unknown library: {library}")
                optimization_time = time.perf_counter() - start
                results[limit][str(method)] = (optimization_time, objective)
                if saved_objective == -1:
                    saved_objective = objective
                elif saved_objective is None or abs(saved_objective - objective) > 1e-3:
                    print("different result", method, limit, saved_objective, objective)
    with BENCHMARK_RESULTS.open("w") as f:
        json.dump(results, f, indent=4)
