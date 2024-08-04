SHELL := /bin/bash
DATA_DIR = $(shell realpath data)
OFF_USERNAME = "albert27"


all-fetch: prices-fetch products-fetch ciqual-fetch recommendations-fetch

all: products-summarize recommendations-extract recommendations-summarize-general optimize

prices-fetch:
	DATA_DIR=$(DATA_DIR) OWNER=$(OFF_USERNAME) SIZE=100 python scripts/prices_fetch.py

prices: prices-fetch

products-fetch:
	DATA_DIR=$(DATA_DIR) python scripts/products_fetch.py

ciqual-fetch:
	DATA_DIR=$(DATA_DIR) python scripts/ciqual_fetch.py

products-summarize:
	DATA_DIR=$(DATA_DIR) python scripts/products_summarize.py

products: products-fetch ciqual-fetch products-summarize

recommendations-fetch:
	DATA_DIR=$(DATA_DIR) python scripts/recommendations_fetch.py

recommendations-extract:
	DATA_DIR=$(DATA_DIR) python scripts/recommendations_extract_tables.py

recommendations-summarize-age:
	DATA_DIR=$(DATA_DIR) python scripts/recommendations_summarize_per_age.py

recommendations-summarize-general:
	DATA_DIR=$(DATA_DIR) python scripts/recommendations_summarize_general.py

recommendations: recommendations-fetch recommendations-extract recommendations-summarize-general

optimize:
	DATA_DIR=$(DATA_DIR) python scripts/combine_and_optimize.py

dashboard:
	DATA_DIR=$(DATA_DIR) python scripts/app.py

clean:
	rm -r $(DATA_DIR)/*.csv
