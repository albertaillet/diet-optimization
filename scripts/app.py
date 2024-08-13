"""This script combines the different summarized csv files and creates a dashboard to interact
with linear optimization to get the optimal quantities of food products.

Usage of script DATA_DIR=<path to data directory> OFF_USERNAME=<yourusername> python app.py

TODO: Include other objectives than price minimization with tunable hyperparameters.
TODO: Choose to include maximum values even when they are not available in recommendations.
TODO: Include breakdown source of each nutrient (either in popup, other page or in generated pdf).
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

from utils.table import inner_merge

DATA_DIR = Path(os.getenv("DATA_DIR", ""))
OFF_USERNAME = os.getenv("OFF_USERNAME")

CURRENCY_DROPDOWN_ID = "currency-dropdown"
MACRONUTRIENT_RESET_ID = "button-macronutrient-reset"
DROPDOWN_MACRONUTRIENT_CHOICE_ID = "dropdown-macronutrient-choice"
MICRONUTRIENT_RESET_ID = "button-micronutrient-reset"
DROPDOWN_MICRONUTRIENT_CHOICE_ID = "dropdown-micronutrient-choice"
SLIDER_TABLE_ID = "slider-table"
SLIDER_TYPE_ID = "slider"
RESULT_TABLE_ID = "result-table"

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


def get_arrays(
    bounds: dict[str, dict[str, str | float]], products_and_prices: dict[str, list[str | float]], currency: str
) -> tuple[np.ndarray, ...]:
    # Check that the upper and lower bounds nutrients use the same units as the product nutrients.
    for nutrient in bounds:
        product_unique_units = set(products_and_prices[nutrient + "_unit"])
        recommendation_unit = bounds[nutrient]["unit"]
        assert product_unique_units == {recommendation_unit}, (nutrient, product_unique_units, recommendation_unit)

    # Nutrients of each product
    A_nutrients = np.array([products_and_prices[nutrient + "_value"] for nutrient in bounds], dtype=np.float32)

    # Costs of each product (* 0.1 to go from price per kg to price per 100g)
    c_costs = 0.1 * np.array(products_and_prices[f"price_{currency.lower()}"], dtype=np.float32)

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


def create_rangeslider(data: dict[str, str], *, micro=False) -> dcc.RangeSlider:
    """Create the rangeslider of the given nutrient with the given data."""
    value_key = "value_males"  # "value_females"  # NOTE: using male values
    lower = convert_to_int_if_possible(float(data[value_key]))
    upper = convert_to_int_if_possible(float(data["value_upper_intake"])) if data["value_upper_intake"] != "" else None
    _min = 0 if data["off_id"] != "energy-kcal" else 1000
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
        id={"type": SLIDER_TYPE_ID, "off_id": data["off_id"], "unit": unit},
        persistence=True,
    )


def extract_slider_values(
    slider_values: list[list[float]], slider_ids: list[dict[str, str]]
) -> dict[str, dict[str, float | str]]:
    return {
        slider_id["off_id"]: {
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


def filter_nutrients(
    nutrient_map: list[dict[str, str]], recommendations: list[dict[str, str]]
) -> tuple[list[dict[str, str]], list[str]]:
    available_recommendations = {rec["off_id"] for rec in recommendations}
    filtered_nutrient_map = [row for row in nutrient_map if row["off_id"] in available_recommendations]
    used = [{"label": row["ciqual_name"], "value": row["off_id"], "search": row["ciqual_id"]} for row in filtered_nutrient_map]
    default_values = [row_dict["off_id"] for row_dict in filtered_nutrient_map]
    return used, default_values


def create_app(
    macro_recommendations: list[dict[str, str]],
    micro_recommendations: list[dict[str, str]],
    products_and_prices: dict[str, list[str | float]],
    nutrient_map: list[dict[str, str]],
) -> Dash:
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    currency_dropdown = dcc.Dropdown(
        options=POSSIBLE_CURRENCIES, value=POSSIBLE_CURRENCIES[0], persistence=True, id=CURRENCY_DROPDOWN_ID, clearable=False
    )

    macronutrient_reset_button = dbc.Button("Reset", id=MACRONUTRIENT_RESET_ID)
    used_macronutrients, default_used_macronutrients_values = filter_nutrients(nutrient_map, macro_recommendations)
    macronutrient_dropdown = dcc.Dropdown(
        options=used_macronutrients,
        value=default_used_macronutrients_values,
        placeholder="Choose macronutrients",
        multi=True,
        persistence=True,
        id=DROPDOWN_MACRONUTRIENT_CHOICE_ID,
    )
    micronutrient_reset_button = dbc.Button("Reset", id=MICRONUTRIENT_RESET_ID)
    used_micronutrients, default_used_micronutrients_values = filter_nutrients(nutrient_map, micro_recommendations)
    micronutrient_dropdown = dcc.Dropdown(
        options=used_micronutrients,
        value=default_used_micronutrients_values,
        placeholder="Choose micronutrients",
        multi=True,
        persistence=True,
        id=DROPDOWN_MICRONUTRIENT_CHOICE_ID,
    )

    app.layout = html.Div([
        dbc.Navbar([
            dbc.Container(html.H1("Dashboard")),
            currency_dropdown,
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
                                html.H4("Optimized Food"),
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
    def reset_macro_dropdown(n_clicks: int) -> list[str]:
        return default_used_macronutrients_values

    @app.callback(
        Output(DROPDOWN_MICRONUTRIENT_CHOICE_ID, "value"),
        Input(MICRONUTRIENT_RESET_ID, "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_micro_dropdown(n_clicks: int) -> list[str]:
        return default_used_micronutrients_values

    @app.callback(
        Output(SLIDER_TABLE_ID, "children"),
        Input(DROPDOWN_MACRONUTRIENT_CHOICE_ID, "value"),
        Input(DROPDOWN_MICRONUTRIENT_CHOICE_ID, "value"),
    )
    def create_chosen_sliders(chosen_macronutrients: list[str], chosen_micronutrients: list[str]) -> html.Tbody:
        macro_rows = [
            html.Tr([
                html.Td(macro["ciqual_name"], className="name-col"),
                html.Td(create_rangeslider(macro), className="slider-col"),
            ])
            for macro in macro_recommendations
            if macro["off_id"] in chosen_macronutrients
        ]
        micro_rows = [
            html.Tr([
                html.Td(micro["nutrient"], className="name-col"),
                html.Td(create_rangeslider(micro, micro=True), className="slider-col"),
            ])
            for micro in micro_recommendations
            if micro["off_id"] in chosen_micronutrients
        ]
        return html.Tbody([
            html.Tr(html.Th("Macronutrients")),
            *macro_rows,
            html.Tr(html.Th("Micronutrients")),
            *micro_rows,
        ])

    @app.callback(
        Output(RESULT_TABLE_ID, "children"),
        Output({"type": SLIDER_TYPE_ID, "off_id": ALL, "unit": ALL}, "marks"),
        Input(CURRENCY_DROPDOWN_ID, "value"),
        Input({"type": SLIDER_TYPE_ID, "off_id": ALL, "unit": ALL}, "value"),
        State({"type": SLIDER_TYPE_ID, "off_id": ALL, "unit": ALL}, "id"),
        State({"type": SLIDER_TYPE_ID, "off_id": ALL, "unit": ALL}, "marks"),
        prevent_initial_call=True,
    )
    def optimize(
        currency: str,
        slider_values: list[list[float]],
        slider_ids: list[dict[str, str]],
        slider_marks: list[dict[str | float, dict[str, str]]],
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
        if len(chosen_bounds) == 0:
            return html.H4("No bounds chosen", className="result-text"), slider_marks

        A_nutrients, lb, ub, c_costs = get_arrays(chosen_bounds, products_and_prices, currency)
        result = solve_optimization(A_nutrients, lb, ub, c_costs)
        if result.status != 0:
            return html.H4("No solution", className="result-text"), slider_marks

        # Caluculate nutrient levels
        nutrients_levels = A_nutrients @ result.x

        # Add marks to the slider to show the current level of that nutrient.
        for slider_mark, nutrients_level in zip(slider_marks, nutrients_levels, strict=True):
            slider_mark[convert_to_int_if_possible(nutrients_level)] = {"label": level_label}

        return [
            html.H5(f"Total price per day: {round(result.fun, 2)} {currency}", className="result-text"),
            dbc.Table(create_result_table(result, products_and_prices, c_costs), striped=True, bordered=False, borderless=True),
        ], slider_marks

    return app


if __name__ == "__main__":
    assert OFF_USERNAME is not None, f"Set OFF_USERNAME env variable {OFF_USERNAME=}"

    with (DATA_DIR / "nutrient_map.csv").open("r") as file:
        nutrient_map = [row_dict for row_dict in csv.DictReader(file) if not row_dict["disabled"]]

    with (DATA_DIR / "user_data" / OFF_USERNAME / "product_prices_and_nutrients.csv").open("r") as file:
        products_and_prices = load_and_filter_products(file, used_nutrients=[row_dict["off_id"] for row_dict in nutrient_map])
    fix_prices(products_and_prices)

    # TODO: fix this to merge the recommendations and nutrient_map correctly
    with (DATA_DIR / "recommendations_macro.csv").open("r") as file:
        macro_recommendations = inner_merge(list(csv.DictReader(file)), nutrient_map, left_key="off_id", right_key="off_id")

    with (DATA_DIR / "recommendations_nnr2023.csv").open("r") as file:
        micro_recommendations = inner_merge(list(csv.DictReader(file)), nutrient_map, left_key="nutrient", right_key="nnr2023_id")

    app = create_app(macro_recommendations, micro_recommendations, products_and_prices, nutrient_map)
    app.run_server(debug=True)
