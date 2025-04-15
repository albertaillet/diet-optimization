#!/usr/bin/env -S uv run
import csv
import difflib
import io
import os
import sys
import tempfile
import timeit

import duckdb


def setup_benchmark_db(rows: int = 100000) -> duckdb.DuckDBPyConnection:
    """Creates a test table with the specified number of rows in a new in-memory database."""
    con = duckdb.connect(":memory:")
    con.execute(
        """
        CREATE TABLE test_data AS
        SELECT
            row_number() OVER () as id,
            concat('name_', (row_number() OVER ())::VARCHAR) as name,
            random() as random_float,
            (random() * 1000)::INTEGER as random_int,
            CASE WHEN random() > 0.7 THEN NULL ELSE 'value_' || (row_number() OVER ())::VARCHAR END as nullable_field
        FROM range(0, $rows)""".replace("$rows", str(rows))
    )
    return con


def method1_duckdb_to_csv(con: duckdb.DuckDBPyConnection, query: str, **kwargs) -> str:
    """Use DuckDB's built-in CSV export. NOTE: newlines are \r\n."""
    fd, name = tempfile.mkstemp(suffix="duckdb.csv")
    con.sql(query, params=kwargs).to_csv(name)
    content = open(name).read()  # noqa: PTH123 SIM115
    os.close(fd)
    os.remove(name)  # noqa: PTH107
    return content


def method2_lists_csv_writer(con: duckdb.DuckDBPyConnection, query: str, **kwargs) -> str:
    """Fetch all and then use csv.writer. NOTE: newlines are \n."""
    con.execute(query, parameters=kwargs)
    fieldnames = [d[0] for d in con.description or []]
    data = con.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(fieldnames)
    writer.writerows(data)
    output.seek(0)
    return output.getvalue()


def method3_dicts_dictwriter(con: duckdb.DuckDBPyConnection, query: str, **kwargs) -> str:
    """Fetch all and then csv.DictWriter. NOTE: newlines are \n."""
    con.execute(query, parameters=kwargs)
    fieldnames = [d[0] for d in con.description or []]
    data = con.fetchall()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows({c: r for c, r in zip(fieldnames, row, strict=True)} for row in data)
    output.seek(0)
    return output.getvalue()


METHOD_NAMES = ["DuckDB's to_csv", "lists + csv.writer", "dicts + csv.DictWriter"]
METHOD_FUNCS = [method1_duckdb_to_csv, method2_lists_csv_writer, method3_dicts_dictwriter]


def run_benchmark(con: duckdb.DuckDBPyConnection, iterations: int, row_counts: list[int]) -> None:
    """Run the benchmark with different dataset sizes."""
    con.execute("""CREATE TABLE IF NOT EXISTS benchmark_results
        ( row_count INTEGER, method VARCHAR, time_ms DOUBLE)""")

    query = "SELECT * FROM test_data"
    for rows in row_counts:
        for method_name, method_func in zip(METHOD_NAMES, METHOD_FUNCS, strict=True):
            con_data = setup_benchmark_db(rows)
            t = timeit.timeit(lambda: method_func(con_data, query), number=iterations) / iterations * 1000  # noqa: B023
            con.execute("INSERT INTO benchmark_results VALUES (?, ?, ?)", [rows, method_name, round(t, 4)])
            con_data.close()
            print(f"{method_name:<25} {rows:>6} {t:>10.4f} ms")


def diff(string1: str, string2: str) -> tuple[bool, str]:
    """Generate a diff between two strings."""
    lines1, lines2 = [[line.replace("\r", "") for line in string.split("\n")] for string in (string1, string2)]
    ndiff = difflib.ndiff(lines1, lines2)
    d = any(line.startswith(("+ ", "- ")) for line in ndiff)
    return d, "\n".join(ndiff)


def verify_outputs_match():
    """Verify that all methods produce the same output."""
    print("Verifying output consistency...")
    con = setup_benchmark_db(10)  # Small table for verification
    query = "SELECT * FROM test_data"
    out1 = METHOD_FUNCS[0](con, query)
    all_match = True
    for method_func in METHOD_FUNCS[1:]:
        out2 = method_func(con, query)
        d, diff_output = diff(out1, out2)
        if d:
            all_match = False
            print(f"Outputs differ for {method_func.__name__}:\n", diff_output)
    if all_match:
        print("All outputs match.")


if __name__ == "__main__":
    print(f"Python {sys.version}")
    print(f"DuckDB {duckdb.__version__}")
    verify_outputs_match()
    results_db = duckdb.connect(":memory:")  # One in-memory DB (results_db) to store the benchmark results.
    row_counts = [10, 50, 100, 1000, 2000, 3000, 5000, 10000, 100000]
    iterations = 100
    run_benchmark(iterations=iterations, row_counts=row_counts, con=results_db)
    # results_db.sql("""SELECT * FROM benchmark_results ORDER BY row_count, time_ms ASC""").show()
    print("\nFastest method for each row_count:")
    q = """SELECT DISTINCT ON (row_count) row_count, method, time_ms FROM benchmark_results ORDER BY row_count, time_ms ASC"""
    results_db.sql(q).show()

# Python 3.13.2 (main, Feb  4 2025, 14:51:09) [Clang 16.0.0 (clang-1600.0.26.6)]
# DuckDB 1.2.1
# Verifying output consistency...
# All outputs match.
# DuckDB's to_csv               10     2.4945 ms
# lists + csv.writer            10     0.1214 ms
# dicts + csv.DictWriter        10     0.1077 ms
# DuckDB's to_csv               50     3.3007 ms
# lists + csv.writer            50     0.2088 ms
# dicts + csv.DictWriter        50     0.1921 ms
# DuckDB's to_csv              100     2.8764 ms
# lists + csv.writer           100     0.2856 ms
# dicts + csv.DictWriter       100     0.2702 ms
# DuckDB's to_csv             1000     2.8200 ms
# lists + csv.writer          1000     1.2209 ms
# dicts + csv.DictWriter      1000     1.8640 ms
# DuckDB's to_csv             2000     2.9359 ms
# lists + csv.writer          2000     2.2581 ms
# dicts + csv.DictWriter      2000     3.7158 ms
# DuckDB's to_csv             3000     3.1746 ms
# lists + csv.writer          3000     3.3084 ms
# dicts + csv.DictWriter      3000     5.5475 ms
# DuckDB's to_csv             5000     3.5353 ms
# lists + csv.writer          5000     5.3849 ms
# dicts + csv.DictWriter      5000     9.2944 ms
# DuckDB's to_csv            10000     4.7425 ms
# lists + csv.writer         10000    10.6070 ms
# dicts + csv.DictWriter     10000    18.4971 ms
# DuckDB's to_csv           100000    23.0254 ms
# lists + csv.writer        100000   114.9140 ms
# dicts + csv.DictWriter    100000   193.1870 ms

# Fastest method for each row_count:
# ┌───────────┬────────────────────────┬─────────┐
# │ row_count │         method         │ time_ms │
# │   int32   │        varchar         │ double  │
# ├───────────┼────────────────────────┼─────────┤
# │        10 │ dicts + csv.DictWriter │  0.1077 │
# │        50 │ dicts + csv.DictWriter │  0.1921 │
# │       100 │ dicts + csv.DictWriter │  0.2702 │
# │      1000 │ lists + csv.writer     │  1.2209 │
# │      2000 │ lists + csv.writer     │  2.2581 │
# │      3000 │ DuckDB's to_csv        │  3.1746 │
# │      5000 │ DuckDB's to_csv        │  3.5353 │
# │     10000 │ DuckDB's to_csv        │  4.7425 │
# │    100000 │ DuckDB's to_csv        │ 23.0254 │
# └───────────┴────────────────────────┴─────────┘
