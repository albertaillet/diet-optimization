import base64
import json
import os
from pathlib import Path

from dash import Dash, Input, Output, dcc, html

DATA_DIR = Path(os.getenv("DATA_DIR", ""))
BASE_IMAGE_DIR = DATA_DIR / "exported_images"

static_image_route = "/static/"

# TODO: Use this together with a regex to extract a proposed barcode.
# def check_ean13(number: int) -> bool:
#     """Based on https://en.wikipedia.org/wiki/International_Article_Number#Position_%E2%80%93_weight."""
#     num_str = str(number)
#     assert len(num_str) == 13, f"{number} is not 13 digits long."
#     remainder = sum(int(num_str[i]) * (3 if i % 2 else 1) for i in range(12)) % 10
#     check_digit = 10 - remainder if remainder else 0
#     return int(num_str[-1]) == check_digit


def create_app(list_of_images: list[Path]) -> Dash:
    app = Dash()

    options = list(sorted(p.name for p in list_of_images))

    app.layout = html.Div([
        dcc.Dropdown(id="image-dropdown", options=options, value=options[0]),
        html.Img(id="image"),
        html.Div(id="image_path"),
        html.Div(id="output"),
    ])

    @app.callback(
        Output("image", "src"),
        Output("image_path", "children"),
        Output("output", "children"),
        Input("image-dropdown", "value"),
    )
    def update_image_desc(image_filename: str):
        with (BASE_IMAGE_DIR / image_filename).open("rb") as f:
            b64_string = "data:image/png;base64," + base64.b64encode(f.read()).decode()
        with (BASE_IMAGE_DIR / image_filename).with_suffix(".json").open("r") as f:
            d = json.load(f)
        responses = d["responses"]
        assert len(responses) == 1, len(responses)
        annotations = responses[0]["textAnnotations"]
        return b64_string, str(BASE_IMAGE_DIR / image_filename), [html.Div(ann["description"]) for ann in annotations]

    return app


if __name__ == "__main__":
    list_of_images = [p for p in BASE_IMAGE_DIR.glob("*.png") if p.with_suffix(".json").exists()]

    app = create_app(list_of_images)
    app.run_server(debug=True)
