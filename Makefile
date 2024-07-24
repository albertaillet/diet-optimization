SHELL := /bin/bash
DATA_DIR = $(shell realpath data)

all: prices products nutritents

prices-fetch:
	DATA_DIR=$(DATA_DIR) OWNER=albert27 SIZE=100 python scripts/prices_fetch.py

prices-summarize:
	DATA_DIR=$(DATA_DIR) python scripts/prices_summarize.py

prices: prices prices-summarize


products-fetch:
	DATA_DIR=$(DATA_DIR) python scripts/products_extract.py

products-summarize:
	DATA_DIR=$(DATA_DIR) python scripts/products_summarize.py

products: products products-summarize

clean:
	rm -r $(DATA_DIR)/*.csv
