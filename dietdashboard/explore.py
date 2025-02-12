# %%
from pathlib import Path

import duckdb

# %%
data_path = Path.cwd().parent / "data"
# %%
parquet_path = data_path / "prices.parquet"

# %%
duckdb.sql(f"SELECT * FROM read_parquet('{parquet_path}') LIMIT 1").show()

# %%
duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{parquet_path}')").show()

# %%
owner_id = duckdb.sql(f"""
    WITH data AS (SELECT * FROM read_parquet('{parquet_path}')),
    swiss_owners AS (
        SELECT DISTINCT owner
        FROM data
        WHERE location_osm_address_country = 'Schweiz/Suisse/Svizzera/Svizra'
    ),
    french_owners AS (
        SELECT DISTINCT owner
        FROM data
        WHERE location_osm_address_country = 'France'
    )
    SELECT swiss_owners.owner
    FROM swiss_owners
    INNER JOIN french_owners ON swiss_owners.owner = french_owners.owner
    LIMIT 1
""").fetchone()
assert owner_id is not None
owner_id = owner_id[0]

# %%
duckdb.sql(f"""
    SELECT location_osm_address_city
    FROM read_parquet('{parquet_path}')
    WHERE owner = '{owner_id}'
""").show()

# %%
