#!/usr/bin/env -S uv run --extra benchmark
"""This script benchmarks differency methods for running linear programming"""

import cProfile
import csv
import json
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import cvxpy as cp
import numpy as np
from scipy.optimize import linprog

DATA_DIR = Path(__file__).parent.parent / "data"
BENCHMARK_DATA = DATA_DIR / "benchmark.npz"
BENCHMARK_DIR = Path(__file__).parent.parent / f"tmp/benchmark/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
BENCHMARK_RESULT_SUMMARY = BENCHMARK_DIR / "benchmark_results.csv"


warnings.filterwarnings("ignore", category=DeprecationWarning)  # filter scipy DeprecationWarning

# def save_benchmark_data():
#     import duckdb
#     QUERY = (Path(__file__).parent.parent / "dietdashboard/queries/query.sql").read_text()
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


def solve_optimization_scipy(A, lb, ub, c, solver, solver_options):
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
    return linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None), method=solver, options=solver_options, integrality=0)


def solve_optimization_cvxpy(A, lb, ub, c, solver, solver_options):
    x = cp.Variable(c.shape[0])
    objective = cp.Minimize(c @ x)
    constraints = [x >= 0, A[~np.isnan(lb)] @ x >= lb[~np.isnan(lb)], A[~np.isnan(ub)] @ x <= ub[~np.isnan(ub)]]
    prob = cp.Problem(objective, constraints)
    return prob.solve(solver=solver, **solver_options)


def main(library: str, solver: str, solver_options: dict[str, Any], size: int, iterations: int) -> list[float]:
    objectives = []
    # n = A_nutrients.shape[1]
    # different slice each time to avoid any possible caching
    # s = slice((i * size) % n, ((i + 1) * size) % n, 1 if (i * size) % n < ((i + 1) * size) % n else -1)
    for _ in range(iterations):
        s = slice(0, size)
        A = A_nutrients[:, s]
        c = c_costs[s]
        if library == "scipy":
            out = solve_optimization_scipy(A, lb, ub, c, solver, solver_options)
            objective = float(out.fun)
        elif library == "cvxpy":
            out = solve_optimization_cvxpy(A, lb, ub, c, solver, solver_options)
            objective = float(out)  # type: ignore
        else:
            raise ValueError(f"Unknown library: {library}")
        objectives.append(objective)
    return objectives


def save_results_as_csv(resluts: dict[tuple[str, str, str], tuple[float, int]]):
    with BENCHMARK_RESULT_SUMMARY.open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["size", "solver", "solver_options", "time", "iterations"])
        for (size, solver, solver_options), (t, iterations) in resluts.items():
            writer.writerow([size, solver, solver_options, t, iterations])


if __name__ == "__main__":
    # save_benchmark_data()
    bounds = json.load((DATA_DIR / "input.json").open())
    # bounds = {k: bounds[k] for k in ["energy_fibre_kcal", "protein", "carbohydrate", "fat"]}
    products_and_prices = np.load(BENCHMARK_DATA)
    A_nutrients, lb, ub, c_costs = get_arrays(bounds, products_and_prices)  # type: ignore
    solvers = [
        # library cvxpy:
        # Documentation: https://www.cvxpy.org/tutorial/solvers/index.html#choosing-a-solver
        # See https://github.com/cvxpy/cvxpy/blob/master/pyproject.toml for the dependencies for each solver
        # ("cvxpy", "CBC", {}),
        ("cvxpy", "CLARABEL", {}),  # clarabel settings: clarabel.DefaultSettings
        # ("cvxpy", "COPT", {}),  # not sure how to install COPT
        # ("cvxpy", "DAQP", {}),
        # ("cvxpy", "GLOP", {}),
        ("cvxpy", "GLPK", {}),
        # ("cvxpy", "GLPK_MI", {}),  # uses MIP
        # ("cvxpy", "OSQP", {}),
        # ("cvxpy", "PIQP", {}),
        # ("cvxpy", "PROXQP", {}),
        # ("cvxpy", "PDLP", {}),
        # ("cvxpy", "CPLEX", {}),
        # ("cvxpy", "NAG", {}),
        # ("cvxpy", "ECOS", {}),
        # ("cvxpy", "GUROBI", {}),  # requires license
        ("cvxpy", "MOSEK", {}),  # requires license
        ("cvxpy", "CVXOPT", {}),  # no MIP
        # ("cvxpy", "SDPA", {}),
        ("cvxpy", "SCS", {}),
        ("cvxpy", "SCIP", {}),
        # ("cvxpy", "XPRESS", {}),
        ("cvxpy", "SCIPY", {"scipy_options": {"method": "highs"}}),
        ("cvxpy", "SCIPY", {"scipy_options": {"method": "highs-ds"}}),
        ("cvxpy", "SCIPY", {"scipy_options": {"method": "highs-ipm"}}),
        # ("cvxpy", "SCIPY", {"scipy_options": {"method": "interior-point"}}),  # not working, since matrices are sparse in cvxpy
        # ("cvxpy", "SCIPY", {"scipy_options": {"method": "revised simplex"}}),
        # ("cvxpy", "SCIPY", {"scipy_options": {"method": "simplex"}}),
        ("cvxpy", "HIGHS", {}),
        # library scipy:
        ("scipy", "highs", {}),
        ("scipy", "highs-ds", {}),
        ("scipy", "highs-ipm", {}),
        ("scipy", "interior-point", {}),
        ("scipy", "revised simplex", {}),
        ("scipy", "simplex", {"maxiter": 10_000}),
    ]
    # Currently best:
    # GLPK_MI for MIP and speed
    # scipy interior-point or revised simplex for LP and speed

    sizes = [100, 200, 500, 1000, 2000, 5000, 10000]
    num_iterations = 10
    very_slow_solvers = {
        ("cvxpy", "CVXOPT"),
        ("cvxpy", "SCIPY"),
        ("cvxpy", "SCS"),
        ("scipy", "highs"),
        ("scipy", "highs-ds"),
        ("scipy", "highs-ipm"),
    }

    csv_file = BENCHMARK_RESULT_SUMMARY.open("w")
    writer = csv.writer(csv_file)
    writer.writerow(["library", "solver", "solver_options", "size", "time", "iterations"])

    for size in sizes:
        # calculate the baseline output
        excpected_out = main("cvxpy", "GLPK", {}, size, num_iterations)
        print(f"Baseline output for size {size}: {excpected_out}")

        for library, solver, solver_options in solvers:
            if size > 500 and (library, solver) in very_slow_solvers:
                print(f"Skipping {solver} for size {size}")
                continue
            # warm up the solver
            main(library, solver, solver_options, size, 1)
            filename = f"benchmark_{library}_{solver}_{size}.out"

            start = time.perf_counter()
            profiler = cProfile.Profile()
            profiler.enable()
            out = main(library, solver, solver_options, size, num_iterations)
            profiler.disable()
            optimization_time = (time.perf_counter() - start) / num_iterations
            if size == max(sizes):
                profiler.dump_stats(BENCHMARK_DIR / filename)
                print(f"Results saved to {filename}")
            else:
                print(f"Ran {library} {solver} {size}")
            profiler.clear()

            writer.writerow([library, solver, json.dumps(solver_options), size, optimization_time, num_iterations])
            csv_file.flush()

            for e, g in zip(excpected_out, out, strict=True):
                assert np.isclose(e, g, rtol=1e-2), f"Expected {e} but got {g}"

    csv_file.close()
