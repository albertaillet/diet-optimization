SHELL := /bin/bash
DATA_DIR = $(shell realpath data)


all-fetch: prices-fetch products-fetch ciqual-fetch

all: products-summarize

prices-fetch:
	DATA_DIR=$(DATA_DIR) SIZE=100 python scripts/prices_fetch.py

products-fetch:
	DATA_DIR=$(DATA_DIR) python scripts/products_fetch.py

ciqual-fetch:
	DATA_DIR=$(DATA_DIR) python scripts/ciqual_fetch.py

products-summarize:
	DATA_DIR=$(DATA_DIR) python scripts/products_summarize.py

recommendations-fetch:
	DATA_DIR=$(DATA_DIR) python scripts/recommendations_nnr2023/recommendations_fetch.py

recommendations-extract:
	DATA_DIR=$(DATA_DIR) python scripts/recommendations_nnr2023/recommendations_extract_tables.py

recommendations-summarize-age:
	DATA_DIR=$(DATA_DIR) python scripts/recommendations_nnr2023/recommendations_summarize_per_age.py

recommendations-summarize-general:
	DATA_DIR=$(DATA_DIR) python scripts/recommendations_nnr2023/recommendations_summarize_general.py

recommendations: recommendations-fetch recommendations-extract recommendations-summarize-general

dashboard:
	DATA_DIR=$(DATA_DIR) python scripts/app.py

clean:
	rm -r $(DATA_DIR)/*.csv
