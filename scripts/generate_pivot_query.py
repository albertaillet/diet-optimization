# %%
import os
from pathlib import Path

import duckdb

DATA_DIR = Path(os.getenv("DATA_DIR", "../data")).resolve()
calnut_1 = DATA_DIR / "calnut.1.csv"

con = duckdb.connect()
con.execute(f"CREATE TABLE calnut_1 AS SELECT * FROM read_csv('{calnut_1}')")

# Check for duplicate combinations of ALIM_CODE and CONST_LABEL
duplicates = con.sql("SELECT COUNT(*) FROM calnut_1 GROUP BY ALIM_CODE, CONST_LABEL HAVING COUNT(*) != 1").fetchall()
assert len(duplicates) == 0, "Found duplicate combinations of ALIM_CODE and CONST_LABEL"


def make_pivot_column(label, stat):
    if stat == "combl":
        return f"MAX(CAST(CASE WHEN CONST_LABEL = '{label}' THEN combl END AS INT)) as {label}_combl"
    return f"MAX(CAST(CASE WHEN CONST_LABEL = '{label}' THEN REPLACE({stat}, ',', '.') END AS FLOAT)) as {label}_{stat}"


const_labels = con.sql("SELECT DISTINCT CONST_LABEL FROM calnut_1 ORDER BY CONST_LABEL").fetchall()
assert len(const_labels) == 62, "Expected 62 unique CONST_LABELs"
pivot_expressions = ",\n".join([
    make_pivot_column(label[0], stat) for label in const_labels for stat in ["lb", "mean", "ub", "combl"]
])
print(pivot_expressions)
