#!/usr/bin/env -S uv run
from pathlib import Path

import duckdb

REPO_DIR = Path(__file__).parent.parent
# QUERY_PATH = REPO_DIR / "queries/price_at_locations_comparison.sql"
QUERY_PATH = REPO_DIR / "queries/price_at_locations.sql"

# Hardcoded locations
locations = (601, 602, 627, 628, 629, 632, 633, 2211)  # 2208, 2228, 2229
query = QUERY_PATH.read_text().replace("$locations", str(locations))
with duckdb.connect(REPO_DIR / "data/data.db", read_only=True) as con:
    con.sql(query).show(max_rows=41)  # type: ignore
