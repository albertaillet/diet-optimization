"""This script creates an interface to easily compare the most nutrient-dense products of cetrain categories.

Usage of script DATA_DIR=<path to data directory> python _.py
"""

import csv
import os
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

DATA_DIR = Path(os.getenv("DATA_DIR", ""))
OFF_USERNAME = os.getenv("OFF_USERNAME")

Y_RESET_ID = "button-y-reset"
DROPDOWN_Y_CHOICE_ID = "dropdown-y-choice"
X_RESET_ID = "button-x-reset"
DROPDOWN_X_CHOICE_ID = "dropdown-x-choice"
BAR_GRAPH_ID = "bar-graph"

POSSIBLE_CURRENCIES = ["EUR", "CHF"]


def load_and_filter_products(file, used_nutrients: list[str]) -> dict[str, list[str | float]]:
    """Filters to only the relevant nutrients and drops all products with missing values."""
    product_cols = {"product_code": str, "product_name": str, "ciqual_code": str, "ciqual_name": str}
    price_cols = {"price": float, "currency": str, "price_date": str, "location": str, "location_osm_id": str}
    nutrient_cols = {
        name + suffix: _type for name in used_nutrients for suffix, _type in (("_value", float), ("_unit", str), ("_source", str))
    }
    cols = product_cols | price_cols | nutrient_cols

    products = {col: [] for col in cols}  # Column-oriented dict.
    for row in csv.DictReader(file):
        # Filter out rows where any values are missing.
        if any(row[col] == "" for col in cols):
            continue
        # Filter out rows with unsupported currencies.
        if row["currency"] not in POSSIBLE_CURRENCIES:
            continue
        # Append each of the row values to the correct col, while casting it to _type.
        for col, _type in cols.items():
            products[col].append(_type(row[col]))

    n_rows = len(products["product_code"])
    assert all(len(products[col]) == n_rows for col in products)  # check that all columns have all the rows.

    # Check that all columns have the same unit and that the source are either reported or ciqual.
    for nutient in used_nutrients:
        unique_units = set(products[nutient + "_unit"])
        assert len(unique_units) == 1, (nutient, unique_units)
        unique_sources = set(products[nutient + "_source"])
        assert unique_sources.issubset({"reported", "ciqual"}), (nutient, unique_sources)

    return products


def fix_prices(prices: dict[str, list[str | float]]):
    """Set all prices to the same currency: CHF. Also removes duplicate prices of the same location."""
    EUR_TO_CHF = 0.96  # TODO: fetch this from the internet.
    assert all(c in POSSIBLE_CURRENCIES for c in set(prices["currency"])), set(prices["currency"])
    prices["price_chf"] = [v * EUR_TO_CHF if c == "EUR" else v for v, c in zip(prices["price"], prices["currency"], strict=True)]  # type: ignore
    prices["price_eur"] = [v / EUR_TO_CHF if c == "CHF" else v for v, c in zip(prices["price"], prices["currency"], strict=True)]  # type: ignore


def create_app(
    products_and_prices: dict[str, list[str | float]],
    nutrient_map: list[dict[str, str]],
) -> Dash:
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    possible_cols = [col for col in products_and_prices if all(isinstance(x, float) for x in products_and_prices[col])]

    y_dropdown = dcc.Dropdown(
        options=possible_cols,
        value="energy-kcal_value",
        placeholder="Choose y",
        clearable=False,
        persistence=True,
        id=DROPDOWN_Y_CHOICE_ID,
    )
    x_dropdown = dcc.Dropdown(
        options=possible_cols,
        value="energy-kcal_value",
        placeholder="Choose x",
        clearable=False,
        persistence=True,
        id=DROPDOWN_X_CHOICE_ID,
    )

    app.layout = html.Div([
        dbc.Navbar([dbc.Container(html.H1("Density Dashboard"))]),
        dbc.Container(
            dbc.Row([
                dbc.Col([y_dropdown, x_dropdown, dcc.Graph(id=BAR_GRAPH_ID)]),
            ]),
            fluid=True,
        ),
    ])

    # @app.callback(
    #     Output(DROPDOWN_X_CHOICE_ID, "value"),
    #     Input(X_RESET_ID, "n_clicks"),
    #     prevent_initial_call=True,
    # )
    # def reset_macro_dropdown(n_clicks: int) -> list[str]:
    #     return default_used_macronutrients_values

    # @app.callback(
    #     Output(DROPDOWN_MICRONUTRIENT_CHOICE_ID, "value"),
    #     Input(MICRONUTRIENT_RESET_ID, "n_clicks"),
    #     prevent_initial_call=True,
    # )
    # def reset_micro_dropdown(n_clicks: int) -> list[str]:
    #     return default_used_micronutrients_values

    @app.callback(
        Output(BAR_GRAPH_ID, "figure"),
        Input(DROPDOWN_Y_CHOICE_ID, "value"),
        Input(DROPDOWN_X_CHOICE_ID, "value"),
    )
    def create_bar_chart(x_col: str, y_col: str, top: int = 10) -> go.Figure:
        # Select the reference key for sorting
        # ref_col = products_and_prices[x_col]
        # Get the sorted order of the reference list and keep track of the original indices
        # sorted_indices = sorted(range(len(ref_col)), key=lambda i: ref_col[i], reverse=True)

        # Apply the sorting order to all lists
        # visited = set()
        # data = {"product_name": [], y_col: []}
        # for i in sorted_indices:
        #     product_code = products_and_prices["product_code"][i]
        #     if product_code in visited:
        #         continue
        #     visited.add(product_code)
        #     for key in ["product_name", y_col]:
        #         data[key].append(products_and_prices[key][i])
        #     if len(visited) == top:
        #         break

        return px.scatter(
            products_and_prices,
            x=x_col,
            y=y_col,
            hover_name="product_name",
        )

    return app


if __name__ == "__main__":
    assert OFF_USERNAME is not None, f"Set OFF_USERNAME env variable {OFF_USERNAME=}"

    with (DATA_DIR / "nutrient_map.csv").open("r") as file:
        nutrient_map = [row_dict for row_dict in csv.DictReader(file) if not row_dict["disabled"]]

    with (DATA_DIR / "user_data" / OFF_USERNAME / "product_prices_and_nutrients.csv").open("r") as file:
        products_and_prices = load_and_filter_products(file, used_nutrients=[row_dict["off_id"] for row_dict in nutrient_map])
    fix_prices(products_and_prices)

    app = create_app(products_and_prices, nutrient_map)
    app.run_server(debug=True)
