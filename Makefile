SHELL := /bin/bash
DATA_DIR = $(shell realpath data)

all: prices products nutritents

prices:
	DATA_DIR=$(DATA_DIR) OWNER=albert27 SIZE=100 python scripts/extract_prices.py

products:
	DATA_DIR=$(DATA_DIR) python scripts/extract_products.py

clean:
	rm -r $(DATA_DIR)/*.csv
