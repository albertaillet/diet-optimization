"""This script combines the different summarized csv files and creates a dashboard to interact
with linear optimization to get the optimal quantities of food products.

Usage of script DATA_DIR=<path to data directory> python app.py

TODO: Use both EUR and CHF
TODO: Include other objectives than price minimization with tunable hyperparameters.
TODO: Choose to include maximum values even when they are not available in recommendations.
"""

import csv
import math
import operator
import os
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import numpy as np
from dash import ALL, Dash, Input, Output, State, dcc, html
from scipy.optimize import linprog

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

MACRONUTRIENT_RESET_ID = "button-macronutrient-reset"
DROPDOWN_MACRONUTRIENT_CHOICE_ID = "dropdown-macronutrient-choice"
MICRONUTRIENT_RESET_ID = "button-micronutrient-reset"
DROPDOWN_MICRONUTRIENT_CHOICE_ID = "dropdown-micronutrient-choice"
SLIDER_TABLE_ID = "slider-table"
SLIDER_TYPE_ID = "slider"
RESULT_TABLE_ID = "result-table"

USED_MACRONUTRIENTS = [
    "energy-kcal",
    # "energy-kj",
    # "energy",
    "carbohydrates",
    "proteins",
    "fat",
    "saturated-fat",
    "fiber",
]
USED_MICRONUTRIENTS = [
    # "alcohol",
    # "beta-carotene",
    "calcium",
    # "cholesterol",
    "copper",
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
    "salt",
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


def load_and_filter_products(file, used_nutrients: list[str]) -> dict[str, list[str | float]]:
    """Filters to only the relevant nutrients and drops all products with missing values."""
    product_cols = {"product_code": str, "product_name": str, "ciqual_code": str, "ciqual_name": str}
    price_cols = {"price": float, "currency": str, "price_date": str, "location": str, "location_osm_id": str}
    nutrient_cols = {
        name + suffix: _type for name in used_nutrients for suffix, _type in (("_value", float), ("_unit", str), ("_source", str))
    }
    cols = product_cols | price_cols | nutrient_cols

    reader = csv.DictReader(file)
    products = {col: [] for col in cols}
    for row in reader:
        if any(row[col] == "" for col in cols):
            continue
        for col, _type in cols.items():
            products[col].append(_type(row[col]))

    n_rows = len(products["product_code"])
    assert all(len(products[col]) == n_rows for col in products)  # check that all columns have all the rows.

    # Check that all columns have the same unit and source between rows.
    for nutient in used_nutrients:
        unique_units = set(products[nutient + "_unit"])
        assert len(unique_units) == 1, (nutient, unique_units)
        unique_sources = set(products[nutient + "_source"])
        # Fiber, calcium and salt are sometimes reported and sometimes estimated by ciqual
        if nutient in ("fiber", "calcium", "salt"):
            assert unique_sources == {"reported", "ciqual"}, (nutient, unique_sources)
            continue
        assert len(unique_sources) == 1, (nutient, unique_sources)

    return products


def fix_prices(prices: dict[str, list[str | float]]):
    """Set all prices to the same currency: CHF. Also removes duplicate prices of the same location."""
    EUR_TO_CHF = 0.96  # TODO: fetch this from the internet.
    assert all(c in {"EUR", "CHF"} for c in set(prices["currency"])), set(prices["currency"])
    prices["price_chf"] = [v * EUR_TO_CHF if c == "EUR" else v for v, c in zip(prices["price"], prices["currency"], strict=True)]  # type: ignore
    prices["price_eur"] = [v / EUR_TO_CHF if c == "CHF" else v for v, c in zip(prices["price"], prices["currency"], strict=True)]  # type: ignore


def get_arrays(
    bounds: dict[str, dict[str, float | str]], products_and_prices: dict[str, list[str | float]]
) -> tuple[np.ndarray, ...]:
    # Check that the upper and lower bounds nutrients use the same units as the product nutrients.
    for nutrient in bounds:
        product_unique_units = set(products_and_prices[nutrient + "_unit"])
        recommendation_unit = bounds[nutrient]["unit"]
        assert product_unique_units == {recommendation_unit}, (nutrient, product_unique_units, recommendation_unit)

    # Nutrients of each product
    A_nutrients = np.array([products_and_prices[nutrient + "_value"] for nutrient in bounds], dtype=np.float32)

    # Costs of each product
    c_costs = 0.1 * np.array(products_and_prices["price_chf"], dtype=np.float32)  # to price per kg to price per 100g

    # Lower bounds for nutrients
    lb = np.array([bounds[nutrient]["lb"] for nutrient in bounds], dtype=np.float32)

    # Upper bounds for nutrients
    ub = np.array([bounds[nutrient]["ub"] for nutrient in bounds], dtype=np.float32)

    return A_nutrients, lb, ub, c_costs


def solve_optimization(A, lb, ub, c):
    # Constraints for lower bounds
    A_ub_lb = -A[~np.isnan(lb)]
    b_ub_lb = -lb[~np.isnan(lb)]

    # Constraints for upper bounds
    A_ub_ub = A[~np.isnan(ub)]
    b_ub_ub = ub[~np.isnan(ub)]

    # Concatenate both constraints
    A_ub = np.vstack([A_ub_lb, A_ub_ub])
    b_ub = np.concatenate([b_ub_lb, b_ub_ub])

    # Solve the problem and result the result.
    return linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None))


def convert_to_int_if_possible(x: float) -> float | int:
    """This is necessary for the marks to show correctly on the slider."""
    return x if x is None else int(x) if x == int(x) else x


def create_rangeslider(data: dict[str, float | str], *, micro=False) -> dcc.RangeSlider:
    """Create the rangeslider of the given nutrient with the given data."""
    value_key = "value_males"  # "value_females"  # NOTE: using male values
    lower = convert_to_int_if_possible(float(data[value_key]))
    upper = convert_to_int_if_possible(float(data["value_upper_intake"])) if data["value_upper_intake"] != "" else None
    _min = 0 if data["nutrient_id"] != "energy-kcal" else 1000
    _max = 4 * lower if upper is None else math.ceil(upper + (lower - _min))
    _max = _min + 100 if _max == _min else _max
    unit = data["unit"]
    marks = {
        _min: {"label": f"{_min}{unit}"},
        _max: {"label": f"{_max}{unit}"},
    }
    if micro:
        marks[lower] = {"label": f"{lower}{unit}", "style": {"color": "#369c36"}}  # type: ignore
    if micro and upper is not None:
        marks[upper] = {"label": f"{upper}{unit}", "style": {"color": "#f53d3d"}}  # type: ignore
    return dcc.RangeSlider(
        min=_min,
        max=_max,
        value=[lower] if upper is None else [lower, upper],
        tooltip={"placement": "bottom", "always_visible": False, "template": f"{{value}}{unit}"},
        marks=marks,
        allowCross=False,
        id={"type": SLIDER_TYPE_ID, "nutrient_id": data["nutrient_id"], "unit": unit},
        persistence=True,
    )


def extract_slider_values(
    slider_values: list[list[float]], slider_ids: list[dict[str, str]]
) -> dict[str, dict[str, float | str]]:
    return {
        slider_id["nutrient_id"]: {
            "lb": slider_value[0],
            "ub": slider_value[1] if len(slider_value) == 2 else np.nan,
            "unit": slider_id["unit"],
        }
        for slider_value, slider_id in zip(slider_values, slider_ids, strict=True)
    }


def create_result_table(result, products_and_prices: dict[str, list[str | float]], c_costs: np.ndarray) -> html.Tbody:
    data_dict_of_lists = {
        "product_code": products_and_prices["product_code"],
        "product_name": products_and_prices["product_name"],
        "ciqual_name": products_and_prices["ciqual_name"],
        "ciqual_code": products_and_prices["ciqual_code"],
        "location": products_and_prices["location"],
        "location_osm_id": products_and_prices["location_osm_id"],
        "quantity_g": (100 * result.x).round(1),
        "price": (c_costs * result.x).round(2),
    }
    cols = data_dict_of_lists.keys()
    data_list_of_dicts = [dict(zip(cols, t, strict=True)) for t in zip(*[data_dict_of_lists[col] for col in cols], strict=True)]

    # Filter on only included products and sort by weight
    sort_by = "quantity_g"
    shown_cols = "Product name", "Ciqual Name", "Location", "Quantity", "Price"
    html_rows = [
        html.Tr([
            html.Td(
                html.A(
                    row_data["product_name"],
                    href=f'https://world.openfoodfacts.org/product/{row_data["product_code"]}',
                    target="_blank",
                    style={"color": "black"},
                )
            ),
            html.Td(
                html.A(
                    row_data["ciqual_name"],
                    href=f'https://ciqual.anses.fr/#/aliments/{row_data["ciqual_code"]}',
                    target="_blank",
                    style={"color": "black"},
                )
            ),
            html.Td(
                html.A(
                    row_data["location"],
                    href=f'https://www.openstreetmap.org/way/{row_data["location_osm_id"]}',
                    target="_blank",
                    style={"color": "black"},
                )
            ),
            html.Td(row_data["quantity_g"]),
            html.Td(row_data["price"]),
        ])
        for row_data in sorted(data_list_of_dicts, key=operator.itemgetter(sort_by), reverse=True)
        if row_data[sort_by] > 0
    ]
    return html.Tbody([html.Tr([html.Th(col) for col in shown_cols]), *html_rows])


def create_app(
    macro_recommendations: list[dict[str, float | str]],
    micro_recommendations: list[dict[str, float | str]],
    products_and_prices: dict[str, list[str | float]],
) -> Dash:
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    macronutrient_reset_button = dbc.Button("Reset", id=MACRONUTRIENT_RESET_ID)
    macronutrient_dropdown = dcc.Dropdown(
        options=USED_MACRONUTRIENTS,
        value=USED_MACRONUTRIENTS,
        placeholder="Choose nutrients",
        multi=True,
        persistence=True,
        id=DROPDOWN_MACRONUTRIENT_CHOICE_ID,
    )
    micronutrient_reset_button = dbc.Button("Reset", id=MICRONUTRIENT_RESET_ID)
    micronutrient_dropdown = dcc.Dropdown(
        options=USED_MICRONUTRIENTS,
        value=USED_MICRONUTRIENTS,
        placeholder="Choose nutrients",
        multi=True,
        persistence=True,
        id=DROPDOWN_MICRONUTRIENT_CHOICE_ID,
    )

    app.layout = html.Div([
        dbc.Navbar([
            dbc.Container(html.H1("Dashboard")),
            macronutrient_reset_button,
            macronutrient_dropdown,
            micronutrient_reset_button,
            micronutrient_dropdown,
        ]),
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
        Output(DROPDOWN_MACRONUTRIENT_CHOICE_ID, "value"),
        Input(MACRONUTRIENT_RESET_ID, "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_macro_dropdown(n_clicks: int):
        return USED_MACRONUTRIENTS

    @app.callback(
        Output(DROPDOWN_MICRONUTRIENT_CHOICE_ID, "value"),
        Input(MICRONUTRIENT_RESET_ID, "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_micro_dropdown(n_clicks: int):
        return USED_MICRONUTRIENTS

    @app.callback(
        Output(SLIDER_TABLE_ID, "children"),
        Input(DROPDOWN_MACRONUTRIENT_CHOICE_ID, "value"),
        Input(DROPDOWN_MICRONUTRIENT_CHOICE_ID, "value"),
    )
    def create_chosen_sliders(chosen_macronutrients: list[str], chosen_micronutrients: list[str]) -> html.Tbody:
        macro_rows = [
            html.Tr([
                html.Td(macro["nutrient"], style={"width": "20%"}),
                html.Td(create_rangeslider(macro), style={"width": "80%"}),
            ])
            for macro in macro_recommendations
            if macro["nutrient_id"] in chosen_macronutrients
        ]
        micro_rows = [
            html.Tr([
                html.Td(micro["nutrient"], style={"width": "20%"}),
                html.Td(create_rangeslider(micro, micro=True), style={"width": "80%"}),
            ])
            for micro in micro_recommendations
            if micro["nutrient_id"] in chosen_micronutrients
        ]
        return html.Tbody([
            html.Tr(html.Th("Macronutrients")),
            *macro_rows,
            html.Tr(html.Th("Micronutrients")),
            *micro_rows,
        ])

    @app.callback(
        Output(RESULT_TABLE_ID, "children"),
        Output({"type": SLIDER_TYPE_ID, "nutrient_id": ALL, "unit": ALL}, "marks"),
        Input({"type": SLIDER_TYPE_ID, "nutrient_id": ALL, "unit": ALL}, "value"),
        State({"type": SLIDER_TYPE_ID, "nutrient_id": ALL, "unit": ALL}, "id"),
        State({"type": SLIDER_TYPE_ID, "nutrient_id": ALL, "unit": ALL}, "marks"),
        prevent_initial_call=True,
    )
    def optimize(
        slider_values: list[list[float]], slider_ids: list[dict[str, str]], slider_marks: list[dict[str | float, dict[str, str]]]
    ):
        level_label = "▲"

        # Remove previous level markers
        for slider_mark in slider_marks:
            pop_mark = None
            for mark in slider_mark:
                if slider_mark[mark]["label"] == level_label:
                    pop_mark = mark
                    break
            if pop_mark is not None:
                slider_mark.pop(pop_mark)

        chosen_bounds = extract_slider_values(slider_values, slider_ids)
        A_nutrients, lb, ub, c_costs = get_arrays(chosen_bounds, products_and_prices)
        result = solve_optimization(A_nutrients, lb, ub, c_costs)
        if result.status != 0:
            return html.H4("No solution"), slider_marks

        # Caluculate nutrient levels
        nutrients_levels = A_nutrients @ result.x

        # Add marks to the slider to show the current level of that nutrient.
        for slider_mark, nutrients_level in zip(slider_marks, nutrients_levels, strict=True):
            slider_mark[convert_to_int_if_possible(nutrients_level)] = {"label": level_label}

        return [
            html.H5(f"Total price per day: {round(result.fun, 2)}CHF"),
            dbc.Table(create_result_table(result, products_and_prices, c_costs), striped=True, bordered=False, borderless=True),
        ], slider_marks

    return app


if __name__ == "__main__":
    with (DATA_DIR / "product_prices_and_nutrients.csv").open("r") as file:
        products_and_prices = load_and_filter_products(file, USED_MACRONUTRIENTS + USED_MICRONUTRIENTS)
    fix_prices(products_and_prices)

    with (DATA_DIR / "recommendations_macro.csv").open("r") as file:
        macro_recommendations = list(csv.DictReader(file))

    with (DATA_DIR / "recommendations_nnr2023.csv").open("r") as file:
        micro_recommendations = list(csv.DictReader(file))

    app = create_app(macro_recommendations, micro_recommendations, products_and_prices)
    app.run_server(debug=True)
