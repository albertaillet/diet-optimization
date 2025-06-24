SHELL := /bin/sh

# ---------- Ciqual and Calnut tables. ----------

# Documentation:
# Ciuqal: https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20Ciqual%202020_doc_XML_ENG_2020%2007%2007.pdf
# Calnut: https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20CALNUT%202020_doc_FR_2020%2007%2007.pdf
# Ciqual is available at these links:
# https://ciqual.anses.fr/#/cms/download/node/20
# https://www.data.gouv.fr/fr/datasets/table-de-composition-nutritionnelle-des-aliments-ciqual/
# Calnut is available on Open Food Facts:
# https://github.com/openfoodfacts/openfoodfacts-server/tree/main/external-data/ciqual/calnut

CIQUAL_XML_ZIP := data/XML_2020_07_07.zip
$(CIQUAL_XML_ZIP):
	wget -O $(CIQUAL_XML_ZIP) https://ciqual.anses.fr/cms/sites/default/files/inline-files/XML_2020_07_07.zip

CALNUT_0_CSV := data/calnut.0.csv
$(CALNUT_0_CSV):
	wget -O $(CALNUT_0_CSV) https://raw.githubusercontent.com/openfoodfacts/openfoodfacts-server/refs/heads/main/external-data/ciqual/calnut/CALNUT.csv.0

CALNUT_1_CSV := data/calnut.1.csv
$(CALNUT_1_CSV):
	wget -O $(CALNUT_1_CSV) https://raw.githubusercontent.com/openfoodfacts/openfoodfacts-server/refs/heads/main/external-data/ciqual/calnut/CALNUT.csv.1

# Unzip and convert the Ciqual data to csv.
CIQUAL_DIR := data/ciqual2020
unzip-and-process-ciqual: $(CIQUAL_XML_ZIP)
	[ -d $(CIQUAL_DIR) ] && rm -r $(CIQUAL_DIR) || true
	unzip -o $(CIQUAL_XML_ZIP) -d $(CIQUAL_DIR)
	./scripts/xml_to_csv.py $(CIQUAL_DIR)/alim_2020_07_07.xml $(CIQUAL_DIR)/alim.csv
	./scripts/xml_to_csv.py $(CIQUAL_DIR)/alim_grp_2020_07_07.xml $(CIQUAL_DIR)/alim_grp.csv
	./scripts/xml_to_csv.py $(CIQUAL_DIR)/compo_2020_07_07.xml $(CIQUAL_DIR)/compo.csv
	./scripts/xml_to_csv.py $(CIQUAL_DIR)/sources_2020_07_07.xml $(CIQUAL_DIR)/sources.csv
	./scripts/xml_to_csv.py $(CIQUAL_DIR)/const_2020_07_07.xml $(CIQUAL_DIR)/const.csv

# ---------- Agribalyse commands. ----------
# Documentation:
# https://doc.agribalyse.fr/documentation
# Data License: ETALAB Licence Ouverte v2.0

# Available at these links:
# https://data.gouv.fr/datasets?q=AGRIBALYSE (.csv)
# https://data.ademe.fr/datasets?topics=TQJGtxm2_ (multiple formats)
# https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.57745/XTENSJ (.xlsx)
# https://github.com/openfoodfacts/openfoodfacts-server/tree/main/external-data/environmental_score/agribalyse (.csv)

# Sed is used to remove all rows that are empty or contain only commas.
AGRIBALYSE_CSV := data/agribalyse_synthese.csv
$(AGRIBALYSE_CSV):
	wget -O $(AGRIBALYSE_CSV) https://www.data.gouv.fr/fr/datasets/r/41397293-3e85-4959-8936-940bb79d91fc
	sed -i.bak '/^,/d' $(AGRIBALYSE_CSV)
	rm $(AGRIBALYSE_CSV).bak

# To fetch more detailed Agribalyse data:
# wget -O data/agribalyse_ingredient_details.csv https://www.data.gouv.fr/fr/datasets/r/6bd67be2-dea5-446c-bbf5-6fff9a6366c0
# wget -O data/agribalyse_step_details.csv https://www.data.gouv.fr/fr/datasets/r/93b8a0f4-03f4-41d4-8aef-287df16176fd

# ---------- Nutrient map commands. ----------

# Fetch the initial version of the nutrient map from https://github.com/openfoodfacts/recipe-estimator
NUTRIENT_MAP_RE := data/nutrient_map_recipe_estimator.csv
$(NUTRIENT_MAP_RE):
	wget -O $(NUTRIENT_MAP_RE) https://raw.githubusercontent.com/openfoodfacts/recipe-estimator/main/ciqual/nutrient_map.csv

nutrient-map-reformat: $(NUTRIENT_MAP_RE)
	./scripts/nutrient_map/nutrient_map_reformat.py

nutrient-map-update-counts:
	time duckdb < queries/nutrient_map_update_counts.sql

nutrient-map-update-ciqual: $(CALNUT_1_CSV)
	time duckdb < ./queries/nutrient_map_update_ciqual.sql

# ---------- EUR exchange rates from the European Central Bank. ----------

# The reference rates are usually updated at around 16:00 CET every working day.
# Documentation: https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
EXCHANGE_RATES_CSV := data/euro_exchange_rates/latest.csv
$(EXCHANGE_RATES_CSV):
	wget https://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip
	unzip -o eurofxref.zip -d data/euro_exchange_rates/
	rm eurofxref.zip
	./scripts/transpose_exchange_rates.py
clean-exchange-rate:
	rm $(EXCHANGE_RATES_CSV)
fetch-exchange-rates: clean-exchange-rate $(EXCHANGE_RATES_CSV)

# ---------- Open food facts prices and products exports. ----------

# Documentation:
# Open Food Facts data page: https://world.openfoodfacts.org/data
# https://huggingface.co/datasets/openfoodfacts/open-prices
# https://huggingface.co/datasets/openfoodfacts/product-database
# Data License: Open Database License family

PRICES_PARQUET := data/prices.parquet
$(PRICES_PARQUET):
	wget -O $(PRICES_PARQUET) https://huggingface.co/datasets/openfoodfacts/open-prices/resolve/main/prices.parquet

PRODUCTS_PARQUET := data/products.parquet
$(PRODUCTS_PARQUET):
	wget -O $(PRODUCTS_PARQUET) https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/food.parquet
# Possible to use DuckDB, but queries the Hugging Face API too much and gets (HTTP 429 Too Many Requests)
# COPY (
# SELECT code, nutriments, nutriscore_score, product_name, product_quantity, product_quantity_unit, quantity, categories_properties,
# FROM read_parquet('hf://datasets/openfoodfacts/product-database/food.parquet')  -- (https link above also works)
# ) TO 'data/products.parquet' WITH (FORMAT PARQUET);

# PRODUCT_JSONL_GZ := data/openfoodfacts-products.jsonl.gz
# $(PRODUCT_JSONL_GZ):
# 	wget -O $(PRODUCT_JSONL_GZ) https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz

# ---------- Fetch all. ----------

fetch-all: $(CIQUAL_XML_ZIP) $(CALNUT_0_CSV) $(CALNUT_1_CSV) $(PRICES_PARQUET) $(PRODUCTS_PARQUET) $(AGRIBALYSE_CSV) fetch-exchange-rates

# ---------- Fetch, extract and summarize the Recommendations from the Nordic Nutrition Recommendations 2023. ----------
# recommendations_nnr2023.csv is tracked in git but can be regenerated by deleting the file and running
# make data/recommendations_nnr2023.csv

NNR_HTML := data/recommendations_nnr2023.html
NNR_EXTRACTED_TABLES := data/recommendations_nnr2023/*.csv
NNR_SUMMARY_CSV := data/recommendations_nnr2023.csv
# Original URL: https://pub.norden.org/nord2023-003/recommendations.html
# Using a snapshot of 29 July 2024:
$(NNR_HTML):
	wget -O $(NNR_HTML) https://web.archive.org/web/20240729193940/https://pub.norden.org/nord2023-003/recommendations.html

$(NNR_EXTRACTED_TABLES): $(NNR_HTML)
	./scripts/recommendations_nnr2023/recommendations_extract_tables.py

$(NNR_SUMMARY_CSV): $(NNR_EXTRACTED_TABLES)
	./scripts/recommendations_nnr2023/recommendations_summarize_general.py

# ---------- Database commands. ----------

rm-db:
	rm data/data.db

load: $(CALNUT_0_CSV) $(CALNUT_1_CSV) $(PRICES_PARQUET) $(PRODUCTS_PARQUET) $(EXCHANGE_RATES_CSV) nutrient-map-update-ciqual
	time duckdb data/data.db < ./queries/load.sql

process:
	time duckdb data/data.db < ./queries/process.sql

recommendations:
	time duckdb data/data.db < ./queries/recommendations.sql

sendover: load process recommendations
	time duckdb data/sendover_$(shell date +%Y%m%d_%H%M%S).db "\
	ATTACH 'data/data.db' AS data;\
	CREATE TABLE final_table AS SELECT * FROM data.final_table;\
	CREATE TABLE recommendations AS SELECT * FROM data.recommendations;\
	DETACH data;"
# rsync -avz data/sendover_DATE.db host:~/path/to/remote/directory/

data-info:
	./scripts/db_info.py

# ---------- App commands. ----------

static:
	time duckdb data/data.db -readonly < ./queries/static.sql

run-dev:
	@trap "kill 0" EXIT; \
		make frontend-watch & \
		./dietdashboard/app.py & \
	wait

run-gunicorn: frontend-install frontend-bundle static
	nohup uv run gunicorn -w 4 -b 0.0.0.0:8000 'dietdashboard.app:create_app()' >> gunicorn.log 2>&1 &

list-gunicorn:
	pgrep -af "dietdashboard.app"

kill-gunicorn:
	pkill -f "dietdashboard.app"

# ---------- Frontend commands. ----------

frontend-install:
	cd dietdashboard/frontend/js && pnpm install

frontend-bundle:
	cd dietdashboard/frontend && ./bundle.sh

frontend-watch:
	cd dietdashboard/frontend && ./bundle.sh watch

# https://x.com/karpathy/status/1915581920022585597
# pipe this into clipboard
frontend-copy:
	uv run files-to-prompt dietdashboard/frontend \
	-e js -e css -e html \
	--ignore node_modules --ignore d3.js \
	--cxml

# ---------- Create the nutrient extraction template. ----------

template-rename:
	duckdb data/data.db -readonly "SELECT id FROM nutrient_map WHERE calnut_const_code IS NOT NULL" -csv -noheader | awk '{print $$0 "_value AS " $$0 ","}'

# ---------- Queries to view available units. ----------

unit-products:
	duckdb data/data.db -readonly \
	"SELECT p.product_quantity_unit AS unit, count(*) AS count \
	FROM products AS p \
	GROUP BY p.product_quantity_unit ORDER BY count DESC"

# ┌────────┬─────────┐
# │  unit  │  count  │
# ├────────┼─────────┤
# │ NULL   │ 2853258 │
# │ g      │  853132 │
# │ ml     │  151917 │
# │ mmol/l │      21 │
# │ %      │      18 │
# │ kj     │      13 │
# └────────┴─────────┘

unit-nutrients:
	duckdb data/data.db -readonly \
	"SELECT n.unnest.unit as unit, count(*) AS count \
	FROM products, UNNEST(products.nutriments) AS n \
	GROUP BY n.unnest.unit ORDER BY count DESC"

# ┌───────────┬──────────┐
# │   unit    │  count   │
# ├───────────┼──────────┤
# │ g         │ 19830436 │
# │ kcal      │  5286595 │
# │ NULL      │  4613615 │
# │ mg        │  2034441 │
# │           │   996735 │
# │ kJ        │   752115 │
# │ IU        │   185308 │
# │ µg        │   147253 │
# │ % vol     │    44983 │
# │ % DV      │    30690 │
# │ kj        │    19114 │
# │ %         │     3891 │
# │ % vol / * │     1452 │
# │ &#181;g   │      552 │
# │ mcg       │      333 │
# │ vol       │       90 │
# │ 100g      │       56 │
# │ g/100mL   │       41 │
# │ g/100g    │       20 │
# │ Cal       │       19 │
# │ missing   │        8 │
# etc..

unit-ciqual-calnut:
	duckdb data/data.db -readonly "SELECT ciqual_unit, count(*) AS count FROM nutrient_map AS n GROUP BY ciqual_unit ORDER BY count DESC"
	duckdb data/data.db -readonly "SELECT calnut_unit, count(*) AS count FROM nutrient_map AS n GROUP BY calnut_unit ORDER BY count DESC"

# ┌─────────────┬───────┐     ┌─────────────┬───────┐
# │ ciqual_unit │ count │     │ calnut_unit │ count │
# ├─────────────┼───────┤     ├─────────────┼───────┤
# │ g           │    34 │     │ g           │    34 │
# │ mg          │    17 │     │ mg          │    17 │
# │ µg          │     9 │     │ mcg         │     9 │
# │ kj          │     1 │     │ kj          │     1 │
# │ kcal        │     1 │     │ kcal        │     1 │
# └─────────────┴───────┘     └─────────────┴───────┘
