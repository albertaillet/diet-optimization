#!/usr/bin/env -S uv run
"""This script checks the consistency of the currencies in the prices and euro_exchange_rates tables."""

from pathlib import Path

import duckdb

DATA_DIR = Path(__file__).parent.parent / "data"

con = duckdb.connect(DATA_DIR / "data.db")
currencies_in_prices = set(con.execute("""SELECT DISTINCT currency FROM prices ORDER BY currency""").fetchall())
currencies_in_exchanges = set(con.execute("""SELECT DISTINCT currency FROM euro_exchange_rates ORDER BY currency""").fetchall())


def set_difference(set1: set, set2: set) -> str:
    difference = set1 - set2
    return f"{', '.join(d[0] for d in difference)}"


print(f"Currencies in prices but not in euro_exchange_rates:\n{set_difference(currencies_in_prices, currencies_in_exchanges)}")
print(f"Currencies in euro_exchange_rates but not in prices:\n{set_difference(currencies_in_exchanges, currencies_in_prices)}")

# Output:

# Currencies in prices but not in euro_exchange_rates:
# RSD, DZD, RUB, MDL, XPF, AED, UAH, EGP, COP, KHR, PKR, ARS, LBP, MAD, LAK,
# GEL, MRU, PEN, BMD, AMD, TND, KZT, QAR, TWD, BDT, BAN, ADP, XAF, XOF, DDM

# Currencies in euro_exchange_rates but not in prices:
# KRW, THB, ISK
