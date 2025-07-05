#!/usr/bin/env -S uv run

from pathlib import Path

import duckdb
from flask import Flask, render_template

REPO_DIR = Path(__file__).parent.parent
QUERY_PATH = REPO_DIR / "queries/price_at_locations_comparison.sql"
TEMPLATE_FOLDER = REPO_DIR / "dietdashboard/frontend/html"

app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
locations = (601, 602, 627, 628, 629, 632, 633, 2211)  # 2208, 2228, 2229

con = duckdb.connect(REPO_DIR / "data/data.db", read_only=True)

query_names = """
SELECT ANY_VALUE(location_osm_display_name)
  FROM final_table_price
  GROUP BY location_id
  HAVING location_id IN $locations
ORDER BY list_position($locations, location_id)
"""
location_names = [n[0].split(", ")[0] for n in con.sql(query_names, params={"locations": locations}).fetchall()]

query_comparison = QUERY_PATH.read_text().replace("$locations", str(locations))
rows = con.sql(query_comparison).fetchall()

con.close()


@app.route("/")
def index():
    return render_template("comparison.html", location_names=location_names, rows=rows)


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8000)
