"""This script combines the different summarized csv files and creates a dashboard to interact
with linear optimization to get the optimal quantities of food products.

Usage of script DATA_DIR=<path to data directory> OFF_USERNAME=<yourusername> python app.py

TODO: generate results table.
TODO: show/hide sliders depending on the chosen nutrients.
TODO: have link to load info card for each of the chosen products.

Long term todos:
- Retrieve prices in SQL database.
- User authenticaiton.

Todos from dash dashboard
TODO: Include other objectives than price minimization with tunable hyperparameters.
TODO: Choose to include maximum values even when they are not available in recommendations.
TODO: Include breakdown source of each nutrient (either in popup, other page or in generated pdf).
"""

import csv
import math
import os
from pathlib import Path

from flask import Flask, render_template, render_template_string, request

from utils.table import inner_merge

DATA_DIR = Path(os.getenv("DATA_DIR", ""))
OFF_USERNAME = os.getenv("OFF_USERNAME")
POSSIBLE_CURRENCIES = ["EUR", "CHF"]


def create_rangeslider(data: dict[str, str]) -> dict[str, float | str]:
    """Create the rangeslider of the given nutrient with the given data."""
    value_key = "value_males"  # "value_females"  # NOTE: using male values
    lower = float(data[value_key])
    upper = float(data["value_upper_intake"]) if data["value_upper_intake"] != "" else None
    _min = 0 if data["off_id"] != "energy-kcal" else 1000
    _max = 4 * lower if upper is None else math.ceil(upper + lower - _min)
    _max = _min + 100 if _max == _min else _max
    unit = data["unit"]
    # marks = {
    #     _min: {"label": f"{_min}{unit}"},
    #     _max: {"label": f"{_max}{unit}"},
    # }
    # if micro:
    #     marks[lower] = {"label": f"{lower}{unit}", "style": {"color": "#369c36"}}  # type: ignore
    # if micro and upper is not None:
    #     marks[upper] = {"label": f"{upper}{unit}", "style": {"color": "#f53d3d"}}  # type: ignore
    return {
        "name": data["ciqual_name"],
        "id": data["off_id"],
        "unit": unit,
        "min": _min,
        "max": _max,
        "lower": lower,
        "upper": upper if upper is not None else _max,
        # "tooltip": {"placement": "bottom", "always_visible": False, "template": f"{{value}}{unit}"},
        # "marks": marks,
    }


def filter_nutrients(nutrient_map: list[dict[str, str]], recommendations: list[dict[str, str]]) -> list[dict[str, str]]:
    available = {rec["off_id"] for rec in recommendations}
    return [{"name": row["ciqual_name"], "id": row["off_id"]} for row in nutrient_map if row["off_id"] in available]


def create_app(
    macro_recommendations: list[dict[str, str]],
    micro_recommendations: list[dict[str, str]],
    # products_and_prices: dict[str, list[str | float]], TODO
    nutrient_map: list[dict[str, str]],
) -> Flask:
    app = Flask(__name__)

    macronutrients = filter_nutrients(nutrient_map, macro_recommendations)
    micronutrients = filter_nutrients(nutrient_map, micro_recommendations)

    @app.route("/")
    def index():
        nutient_groups = [
            {"name": "Macronutrients", "id": "macro", "nutrients": macronutrients},
            {"name": "Micronutrients", "id": "micro", "nutrients": micronutrients},
        ]
        sliders = [create_rangeslider(rec) for rec in [*macro_recommendations, *micro_recommendations]]
        return render_template(
            "index.html",
            currencies=POSSIBLE_CURRENCIES,
            sliders=sliders,
            nutient_groups=nutient_groups,
        )

    @app.route("/optimize", methods=["POST"])
    def optimize():
        form_data = request.get_json()
        html_template = """
        <table class="table table-striped table-bordered">
            <thead>
                <tr><th>Field</th><th>Value</th></tr>
            </thead>
            <tbody>
                {% for key, value in form_data.items() %}
                <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
        """
        return render_template_string(html_template, form_data=form_data)

    return app


if __name__ == "__main__":
    assert OFF_USERNAME is not None, f"Set OFF_USERNAME env variable {OFF_USERNAME=}"

    with (DATA_DIR / "nutrient_map.csv").open("r") as file:
        nutrient_map = [row_dict for row_dict in csv.DictReader(file) if not row_dict["disabled"]]

    # with (DATA_DIR / "user_data" / OFF_USERNAME / "product_prices_and_nutrients.csv").open("r") as file:
    #     products_and_prices = load_and_filter_products(file, used_nutrients=[row_dict["off_id"] for row_dict in nutrient_map])
    # fix_prices(products_and_prices)

    with (DATA_DIR / "recommendations_macro.csv").open("r") as file:
        macro_recommendations = inner_merge(list(csv.DictReader(file)), nutrient_map, left_key="off_id", right_key="off_id")

    with (DATA_DIR / "recommendations_nnr2023.csv").open("r") as file:
        micro_recommendations = inner_merge(list(csv.DictReader(file)), nutrient_map, left_key="nutrient", right_key="nnr2023_id")

    app = create_app(macro_recommendations, micro_recommendations, nutrient_map)
    app.run(debug=True)
