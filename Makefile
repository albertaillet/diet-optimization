SHELL := /bin/bash
DATA_DIR = $(shell realpath data)
OFF_USERNAME = "albert27"

all: prices products nutrients

prices-fetch:
	DATA_DIR=$(DATA_DIR) OWNER=$(OFF_USERNAME) SIZE=100 python scripts/prices_fetch.py

prices-summarize:
	DATA_DIR=$(DATA_DIR) python scripts/prices_summarize.py

prices: prices-fetch prices-summarize

products-fetch:
	DATA_DIR=$(DATA_DIR) python scripts/products_fetch.py

products-summarize:
	DATA_DIR=$(DATA_DIR) python scripts/products_summarize.py

products: products-fetch products-summarize

nutrients-fetch:
	DATA_DIR=$(DATA_DIR) python scripts/nutrients_fetch.py

nutrients: nutrients-fetch

recommendations:
	DATA_DIR=$(DATA_DIR) python scripts/recommentations_fetch.py

clean:
	rm -r $(DATA_DIR)/*.csv
