"""This script combines the different summarized csv files and creates a dashboard to interact
with linear optimization to get the optimal quantities of food products.

Usage of script DATA_DIR=<path to data directory> python app.py

TODO: show levels of current of diet on the slider markers.
TODO: Use both EUR and CHF
TODO: Include other objectives than price minimization with tunable hyperparameters.
TODO: Choose to include maximum values even when they are not available in recommendations.
TODO: Minimize the use of pandas (I don't like pandas).
TODO: Button to reset dropdown to all available nutrients and another to only macronutrients
"""

import math
import os
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import ALL, Dash, Input, Output, State, dcc, html
from scipy.optimize import linprog

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

DROPDOWN_CHOICE_ID = "dropdown-choice"
SLIDER_TABLE_ID = "slider-table"
SLIDER_TYPE_ID = "slider"
RESULT_TABLE_ID = "result-table"

USED_NUTRIENTS = [
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
    "folate",
    # "fructose",
    # "galactose",
    # "glucose",
    # "iodine",
    "iron",
    # "lactose",
    "magnesium",
    # "maltose",
    # "manganese",
    # "niacin",
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
    "thiamin",
    # "vitamin-a",
    "vitamin-b12",
    "vitamin-b6",
    "vitamin-c",
    # "vitamin-d",  # has multiple units
    "vitamin-e",
    # "vitamin-pp",
    # "water",
    "zinc",
]


def filter_products(products: pd.DataFrame, used_nutrients: list[str]) -> pd.DataFrame:
    """Filters to only the relevant nutrients and drops all products with missing values."""
    product_cols = ["product_code", "product_name", "ciqual_code", "ciqual_name"]
    price_cols = ["price", "currency", "price_date", "location", "location_osm_id"]
    nutrient_cols = [name + suffix for name in used_nutrients for suffix in ("_value", "_unit", "_source")]
    cols = product_cols + price_cols + nutrient_cols
    relevant_products = products[cols].dropna()
    assert relevant_products.shape[1] == len(nutrient_cols) + 9, (relevant_products.shape, len(nutrient_cols) + 9)

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
    assert all(c in {"EUR", "CHF"} for c in prices["currency"].unique()), prices["currency"].unique()
    prices["price_chf"] = prices.apply(lambda r: r["price"] * EUR_TO_CHF if r["currency"] == "EUR" else r["price"], axis=1)
    prices["price_eur"] = prices.apply(lambda r: r["price"] / EUR_TO_CHF if r["currency"] == "CHF" else r["price"], axis=1)
    return prices


def add_hardcoded_additional_recommendations(recommendations: dict[str, dict[str, float | str]]) -> None:
    """Adds macronutrients to the micronutrient recommendation dict."""
    # NOTE: same for males and females
    additional_recommendations_lb_ub_unit = {
        "carbohydrates": (0, np.nan, "g"),
        "fiber": (40, 70, "g"),
        "energy-kcal": (2_500, 3_000, "kcal"),
        "fat": (70, np.nan, "g"),
        "saturated-fat": (0, np.nan, "g"),
        "proteins": (150, np.nan, "g"),
        "salt": (1, 2.3, "g"),
    }
    for nutrient, (lb, ub, unit) in additional_recommendations_lb_ub_unit.items():
        recommendations[nutrient] = {"value_males": lb, "value_females": lb, "value_upper_intake": ub, "unit": unit}


def get_arrays(bounds: dict[str, dict[str, float | str]], products_and_prices: pd.DataFrame) -> tuple[np.ndarray, ...]:
    """From dict of"""
    # Check that the upper and lower bounds nutrients use the same units as the product nutrients.
    for nutrient in bounds:
        product_unique_units = set(products_and_prices[nutrient + "_unit"].unique())
        recommendation_unit = bounds[nutrient]["unit"]
        assert product_unique_units == {recommendation_unit}, (nutrient, product_unique_units, recommendation_unit)

    # Nutrients of each product
    A_nutrients = products_and_prices[[nutrient + "_value" for nutrient in bounds]].values

    # Costs of each product
    c_costs = 0.1 * products_and_prices["price_chf"].values.astype("float")  # to price per kg to price per 100g

    # Lower bounds for nutrients
    lb = np.array([bounds[nutrient]["lb"] for nutrient in bounds])

    # Upper bounds for nutrients
    ub = np.array([bounds[nutrient]["ub"] for nutrient in bounds])

    # lb.shape, ub.shape  # (n_nutrients,)
    return A_nutrients, lb, ub, c_costs


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


def convert_to_int_if_possible(x: float) -> float | int:
    """This is necessary for the marks to show correctly on the slider."""
    return x if np.isnan(x) else int(x) if x == int(x) else x


def create_rangeslider(nutrient: str, data: dict[str, float | str]) -> dcc.RangeSlider:
    """Create the rangeslider of the given nutrient with the given data."""
    value_key = "value_males"  # "value_females"  # NOTE: using male values
    lower = convert_to_int_if_possible(data[value_key])
    upper = convert_to_int_if_possible(data["value_upper_intake"])
    assert not np.isnan(lower), lower
    _min = 0 if nutrient != "energy-kcal" else 1000
    _max = 4 * lower if np.isnan(upper) else math.ceil(upper + (lower - _min))
    _max = _min + 100 if _max == _min else _max
    unit = data["unit"]
    marks = {
        _min: {"label": f"{_min}{unit}"},
        lower: {"label": f"{lower}{unit}", "style": {"color": "#369c36"}},
        _max: {"label": f"{_max}{unit}"},
    }
    if not np.isnan(upper):
        marks[upper] = {"label": f"{upper}{unit}", "style": {"color": "#f53d3d"}}
    return dcc.RangeSlider(
        min=_min,
        max=_max,
        value=[lower] if np.isnan(upper) else [lower, upper],
        tooltip={"placement": "bottom", "always_visible": False, "template": f"{{value}}{unit}"},
        marks=marks,
        allowCross=False,
        id={"type": SLIDER_TYPE_ID, "nutrient": nutrient, "unit": unit},
        persistence=True,
    )


def get_nutrient_slider_row(nutrient: str, data: dict[str, float | str]) -> html.Tr:
    return html.Tr([
        html.Td(nutrient, style={"width": "20%"}),
        html.Td(create_rangeslider(nutrient, data), style={"width": "80%"}),
    ])


def extract_slider_values(
    slider_values: list[list[float]], slider_ids: list[dict[str, str]]
) -> dict[str, dict[str, float | str]]:
    return {
        slider_id["nutrient"]: {
            "lb": slider_value[0],
            "ub": slider_value[1] if len(slider_value) == 2 else np.nan,
            "unit": slider_id["unit"],
        }
        for slider_value, slider_id in zip(slider_values, slider_ids, strict=True)
    }


def create_app(recommendations: dict[str, dict[str, float | str]], products_and_prices: pd.DataFrame) -> Dash:
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    dropdown = dcc.Dropdown(
        options=USED_NUTRIENTS,
        value=USED_NUTRIENTS,
        placeholder="Choose nutrients",
        multi=True,
        persistence=True,
        id=DROPDOWN_CHOICE_ID,
    )

    app.layout = html.Div([
        dbc.Navbar([dbc.Container(html.H1("Dashboard")), dropdown]),
        dbc.Container(
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.CardBody([
                                html.H4("Targets"),
                                html.P("Adjust your nutrient targets to optimize your diet."),
                            ])
                        ]),
                        dbc.CardBody(dbc.Table(id=SLIDER_TABLE_ID, striped=True, bordered=False, borderless=True)),
                    ]),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.CardBody([
                                html.H4("Optimized Meal"),
                                html.P("The recommended food items and quantities to meet your nutrient targets."),
                            ])
                        ]),
                        dbc.CardBody(id=RESULT_TABLE_ID),
                    ]),
                    md=6,
                ),
            ]),
            fluid=True,
        ),
    ])

    @app.callback(
        Output(SLIDER_TABLE_ID, "children"),
        Input(DROPDOWN_CHOICE_ID, "value"),
    )
    def create_chosen_sliders(chosen_nutrients: list[str]):
        return html.Tbody([get_nutrient_slider_row(nutrient, recommendations[nutrient]) for nutrient in chosen_nutrients])

    @app.callback(
        Output(RESULT_TABLE_ID, "children"),
        Input({"type": SLIDER_TYPE_ID, "nutrient": ALL, "unit": ALL}, "value"),
        State({"type": SLIDER_TYPE_ID, "nutrient": ALL, "unit": ALL}, "id"),
        prevent_initial_call=True,
    )
    def optimize(slider_values: list[list[float]], slider_ids: list[dict[str, str]]):
        chosen_bounds = extract_slider_values(slider_values, slider_ids)
        A_nutrients, lb, ub, c_costs = get_arrays(chosen_bounds, products_and_prices)
        result = solve_optimization(A_nutrients, lb, ub, c_costs)
        if result.x is None:
            return html.H4("No solution")
        result_table = pd.DataFrame({
            "product_code": products_and_prices["product_code"],
            "product_name": products_and_prices["product_name"],
            "location": products_and_prices["location"],
            "quantity_g": (100 * result.x).round(2),
            "price_chf": (c_costs * result.x).round(2),
        })
        # Filter on only included products and sort by weight
        result_table = result_table[result_table["quantity_g"] > 0].sort_values(by="quantity_g", ascending=False)
        return [
            html.H5(f"Price per day: {round(result.fun, 4)} CHF"),
            dbc.Table.from_dataframe(result_table, striped=True, bordered=True, hover=True),
        ]

    return app


if __name__ == "__main__":
    products_and_prices = pd.read_csv(DATA_DIR / "product_prices_and_nutrients.csv")
    products_and_prices = filter_products(products_and_prices, USED_NUTRIENTS)
    products_and_prices = fix_prices(products_and_prices)

    recommendations = pd.read_csv(DATA_DIR / "recommendations.csv").set_index("nutrient").to_dict("index")  # type: ignore
    add_hardcoded_additional_recommendations(recommendations)

    app = create_app(recommendations, products_and_prices)
    app.run_server(debug=True)
