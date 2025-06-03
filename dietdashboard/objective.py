#!/usr/bin/env -S uv run
import re

import sqlglot
from sqlglot import expressions as exp
from sqlglot.errors import ParseError

ALLOWED_REGEX = re.compile(r"^[_\w\d+\-*\/%\^&|<>~!@\(\)\.\,\s]+$")
ALLOWED_NODE_TYPES = (exp.Literal, exp.Identifier, exp.Column, exp.Binary, exp.Unary, exp.Func)


def validate_objective_str(objective: str) -> tuple[bool, str]:
    if not ALLOWED_REGEX.match(objective):
        return False, "Expression contains invalid characters. Only alphanumeric, operators, and parentheses are allowed."
    try:
        expression = sqlglot.parse_one(objective, read="duckdb")
    except ParseError as e:
        return False, str(e).split(". ")[0].split("\n")[0]
    return validate_node(expression)


def validate_node(experssion: exp.Expression) -> tuple[bool, str]:
    if not isinstance(experssion, ALLOWED_NODE_TYPES):
        return False, f"Node type {type(experssion).__name__} of {experssion} is not allowed."
    for child in experssion.iter_expressions():
        valid, msg = validate_node(child)
        if not valid:
            return False, msg
    return True, "Valid."


def test_valid(reader):
    for row in reader:
        valid, objective = row["valid"], row["objective"]
        is_valid, msg = validate_objective_str(objective)
        assert is_valid == bool(int(valid)), f"'{objective}', got {is_valid} instead of {valid}, message: {msg}"


if __name__ == "__main__":
    import csv
    from pathlib import Path

    # Valid test cases include all functions and operators supported by DuckDB
    # (https://duckdb.org/docs/stable/sql/functions/numeric.html)
    TEST_FILE = Path(__file__).parent.parent / "data/test_objectives.csv"
    with TEST_FILE.open("r", encoding="utf-8") as f:
        test_valid(csv.DictReader(f))
    print("All tests passed")
