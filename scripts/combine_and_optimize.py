"""This script combine the different summarized csv files and uses linear optimization to get the optimal quantities.

Usage of script DATA_DIR=<data directory> python scripts/combine_and_optimize.py
"""

# %%
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

DATA_DIR = Path("/home/alsundai/git/diet-optimization/data")

used_nutrients = [
    # "alcohol",
    # "beta-carotene",
    "calcium",
    "carbohydrates",
    # "cholesterol",
    "copper",
    "energy-kcal",
    # "energy-kj",
    # "energy",
    "fat",
    "fiber",
    # "fructose",
    # "galactose",
    # "glucose",
    # "iodine",
    "iron",
    # "lactose",
    "magnesium",
    # "maltose",
    # "manganese",
    # "pantothenic-acid",  # has multiple units
    # "phosphorus",  # has multiple units
    # "phylloquinone",
    # "polyols",
    "potassium",
    "proteins",
    "salt",
    "saturated-fat",
    "selenium",
    # "sodium",  # has multiple units
    # "starch",
    # "sucrose",
    # "sugars",
    # "vitamin-a",
    "vitamin-b12",
    # "vitamin-b1",
    # "vitamin-b2",
    "vitamin-b6",
    # "vitamin-b9",
    "vitamin-c",
    # "vitamin-d",  # has multiple units
    "vitamin-e",
    # "vitamin-pp",
    # "water",
    "zinc",
]


def filter_products(products: pd.DataFrame) -> pd.DataFrame:
    """Filters to only the relevant nutrients and drops all products with missing values."""
    cols = ["product_code", "product_name", "ciqual_code"]
    nutrient_cols = [name + suffix for name in used_nutrients for suffix in ("_100g", "_unit", "_source")]
    relevant_products = products[cols + nutrient_cols].dropna()
    # NOTE: temporary check
    assert relevant_products.shape == (26, len(nutrient_cols) + 3), (relevant_products.shape, (25, len(nutrient_cols) + 3))

    # Check that all columns have the same unit and source between rows.
    for nutient in used_nutrients:
        unique_units = relevant_products[nutient + "_unit"].unique()
        assert len(unique_units) == 1, (nutient, unique_units)
        if nutient not in ("fiber", "calcium", "salt"):
            unique_sources = relevant_products[nutient + "_source"].unique()
            assert len(unique_sources) == 1, (nutient, unique_sources)

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


def add_hardcoded_additional_recommendations(recommendations: pd.DataFrame) -> pd.DataFrame:
    indexed_recommendations = recommendations.set_index("nutrient")

    # Adding macronutrients to the micronutrient dataframe.
    # NOTE: same for males and females
    additional_recommendations_lb_ub_unit = {
        "carbohydrates": (0, np.nan, "g"),
        "fiber": (40, 70, "g"),
        "energy-kcal": (2_700, 3_000, "kcal"),
        "fat": (70, np.nan, "g"),
        "saturated-fat": (0, np.nan, "g"),
        "proteins": (150, np.nan, "g"),
        "salt": (1, 2.3, "g"),
    }
    for nutrient, (lb, ub, unit) in additional_recommendations_lb_ub_unit.items():
        indexed_recommendations.loc[nutrient] = [unit, None, lb, lb, ub]

    return indexed_recommendations


def get_recommendations_upper_and_lower_bounds(
    indexed_recommendations: pd.DataFrame, products_and_prices: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray]:
    # Check that the upper and lower bounds nutrients use the same units as the product nutrients.
    for nutrient in used_nutrients:
        product_unique_units = set(products_and_prices[nutrient + "_unit"].unique())
        recommendation_unit = indexed_recommendations.loc[nutrient, "unit"]
        assert product_unique_units == {recommendation_unit}, (nutrient, product_unique_units, recommendation_unit)

    # Lower bounds for nutrients
    value_key = "value_males"  # "value_females"  # NOTE: using male values
    lb = indexed_recommendations[value_key][used_nutrients].values.astype("float")

    # Upper bounds for nutrients
    ub = indexed_recommendations["value_upper_intake"][used_nutrients].values.astype("float")

    # lb.shape, ub.shape  # (n_nutrients,)
    return lb, ub


def solve_optimization(A, lb, ub, c):
    # Constraints for lower bounds
    A_ub_lb = -A.T
    b_ub_lb = -lb

    # Constraints for upper bounds
    A_ub_ub = A.T[~np.isnan(ub)]
    b_ub_ub = ub[~np.isnan(ub)]

    # Concatenate both constraints
    A_ub = np.vstack([A_ub_lb, A_ub_ub])
    b_ub = np.concatenate([b_ub_lb, b_ub_ub])

    # Solve the problem and result the result.
    return linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None))


prices = pd.read_csv(DATA_DIR / "prices.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
recommendations = pd.read_csv(DATA_DIR / "recommendations.csv")

relevant_products = filter_products(products)
fixed_prices = fix_prices(prices)
products_and_prices = pd.merge(relevant_products, fixed_prices, how="inner", on=["product_code", "product_name"])

A_nutrients = products_and_prices[[n + "_100g" for n in used_nutrients]].values

c_costs = 0.1 * products_and_prices["price_chf"].values.astype("float")  # to price per kg to price per 100g

indexed_recommendations = add_hardcoded_additional_recommendations(recommendations)
lb, ub = get_recommendations_upper_and_lower_bounds(indexed_recommendations, products_and_prices)

result = solve_optimization(A_nutrients, lb, ub, c_costs)
result_table = pd.DataFrame({
    "product_code": products_and_prices["product_code"],
    "product_name": products_and_prices["product_name"],
    "location": products_and_prices["location"],
    "quantity_g": (100 * result.x).round(2),
})
print(result_table[result_table["quantity_g"] > 0].head(30))

nutrient_results = A_nutrients.T @ result.x
nutrient_result_table = pd.DataFrame({
    "value": nutrient_results.round(2),
    "unit": indexed_recommendations["unit"][used_nutrients],
})
print(nutrient_result_table)

print("Price per day:", round(result.fun, 4), "CHF")

# %%
