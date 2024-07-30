"""This script combine the different summarized csv files and uses linear optimization to get the optimal quantities.

Usage of script DATA_DIR=<data directory> python scripts/combine_and_optimize.py
"""

# %%
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

DATA_DIR = Path("/home/alsundai/git/diet-optimization/data")

all_estimated_nutrients = [
    # "alcohol",
    # "beta-carotene",
    # "calcium",
    "carbohydrates",
    # "cholesterol",
    # "copper",
    "energy-kcal",
    # "energy-kj",
    # "energy",
    "fat",
    # "fiber",
    # "fructose",
    # "galactose",
    # "glucose",
    # "iodine",
    "iron",
    # "lactose",
    # "magnesium",
    # "maltose",
    # "manganese",
    # "pantothenic-acid",
    # "phosphorus",
    # "phylloquinone",
    # "polyols",
    # "potassium",
    "proteins",
    # "salt",
    # "saturated-fat",
    # "selenium",
    # "sodium",
    # "starch",
    # "sucrose",
    # "sugars",
    # "vitamin-a",
    "vitamin-b12",
    # "vitamin-b1",
    # "vitamin-b2",
    # "vitamin-b6",
    # "vitamin-b9",
    # "vitamin-c",
    # "vitamin-d",
    # "vitamin-e",
    # "vitamin-pp",
    # "water",
    # "zinc",
]
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)


prices = pd.read_csv(DATA_DIR / "prices.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
recommendations = pd.read_csv(DATA_DIR / "recommendations.csv")


def filter_products(products: pd.DataFrame) -> pd.DataFrame:
    """Filters to only the relevant nutrients and drops all products with missing values."""
    cols = ["product_code", "product_name", "ciqual_code"]
    nutrient_cols = [name + suffix for name in all_estimated_nutrients for suffix in ("_100g", "_unit", "_source")]
    relevant_products = products[cols + nutrient_cols].dropna()

    # Check that all columns have the same unit and source between rows.
    for nutient in all_estimated_nutrients:
        assert relevant_products[nutient + "_unit"].nunique() == 1, nutient
        assert relevant_products[nutient + "_source"].nunique() == 1, nutient

    assert relevant_products.shape == (25, 21)  # NOTE: temporary check
    return relevant_products


def fix_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Set all prices to the same currency: CHF. Also removes duplicate prices of the same location."""
    EUR_TO_CHF = 0.96  # TODO: fetch this from the internet.
    assert set(prices["currency"].unique()) == {"EUR", "CHF"}
    prices["price"] = prices.apply(lambda row: EUR_TO_CHF * row["price"] if row["currency"] == "EUR" else row["price"], axis=1)
    # check the "date column" and take the latest price from each product with individual product_id and location_osm_id
    prices["date"] = pd.to_datetime(prices["date"])
    latest_prices = prices.sort_values("date").drop_duplicates(subset=["product_code", "location_osm_id"], keep="last")
    # rename price to price_chf and drop the currency column
    return latest_prices.rename(columns={"price": "price_chf"}).drop(columns=["currency"])


relevant_products = filter_products(products)
fixed_prices = fix_prices(prices)

# %%
products_and_prices = pd.merge(relevant_products, fixed_prices, how="inner", on=["product_code", "product_name"])
products_and_prices.head(40)

# %%
A_nutrients = products_and_prices[[n + "_100g" for n in all_estimated_nutrients]].values
# A_nutrients.shape  # (n_products, n_nutrients)

# %%
c_costs = 0.1 * products_and_prices["price_chf"].values.astype("float")  # to price per kg to price per 100g
# c_costs.shape  # (n_products,)

# %%
# TODO: hardcoded at the moment for testing.
recommendations_lb_ub_unit = {
    "carbohydrates": (0, 200, "g"),
    "energy-kcal": (1_500.0, 3_000.0, "kcal"),
    "fat": (60.0, np.nan, "g"),
    "iron": (9.0, 60.0, "g"),
    "proteins": (120.0, np.nan, "g"),
    "vitamin-b12": (4.0, np.nan, "mg"),
}

# do this and print result using scipy.optimize.linprog
# Lower bounds for nutrients
lb = np.array([recommendations_lb_ub_unit[nutrient][0] for nutrient in all_estimated_nutrients])
ub = np.array([recommendations_lb_ub_unit[nutrient][1] for nutrient in all_estimated_nutrients])
# lb.shape, ub.shape  # (n_nutrients,)

# Constraints for lower bounds
A_ub_lb = -A_nutrients.T
b_ub_lb = -lb

# Constraints for upper bounds
A_ub_ub = A_nutrients.T[~np.isnan(ub)]
b_ub_ub = ub[~np.isnan(ub)]

# Concatenate both constraints
A_ub = np.vstack([A_ub_lb, A_ub_ub])
b_ub = np.concatenate([b_ub_lb, b_ub_ub])

# %% Linear programming to minimize cost
result = linprog(c_costs, A_ub=A_ub, b_ub=b_ub, bounds=(0, None))

# %%
result_table = pd.DataFrame({
    "product_code": products_and_prices["product_code"],
    "product_name": products_and_prices["product_name"],
    "location": products_and_prices["location"],
    "quantity_g": 100 * result.x,
})
print(result_table[result_table["quantity_g"] > 0])

nutrient_results = A_nutrients.T @ result.x
nutrient_result_table = pd.DataFrame({"nutrient": all_estimated_nutrients, "value": nutrient_results})
print(nutrient_result_table)

print("Price per day:", round(result.fun, 4), "CHF")
# %%
