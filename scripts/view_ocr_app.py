import base64
import json
import os
from pathlib import Path

from dash import Dash, Input, Output, dcc, html

DATA_DIR = Path(os.getenv("DATA_DIR", ""))
BASE_IMAGE_DIR = DATA_DIR / "exported_images"

static_image_route = "/static/"


def create_app(list_of_images: list[Path]) -> Dash:
    app = Dash()

    options = [p.name for p in list_of_images]

    app.layout = html.Div([
        dcc.Dropdown(id="image-dropdown", options=options, value=options[0]),
        html.Img(id="image"),
        html.Div(id="image_path"),
        html.Div(id="output"),
    ])

    @app.callback(Output("image", "src"), Input("image-dropdown", "value"))
    def update_image_src(image_filename: str):
        with (BASE_IMAGE_DIR / image_filename).open("rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()

    @app.callback(Output("image_path", "children"), Input("image-dropdown", "value"))
    def update_image_path(image_filename: str):
        return str(BASE_IMAGE_DIR / image_filename)

    @app.callback(Output("output", "children"), Input("image-dropdown", "value"))
    def update_image_desc(image_filename: str):
        with (BASE_IMAGE_DIR / image_filename).with_suffix(".json").open("r") as f:
            d = json.load(f)
        responses = d["responses"]
        assert len(responses) == 1, len(responses)
        annotations = responses[0]["textAnnotations"]
        return [html.Div(ann["description"]) for ann in annotations]

    return app


if __name__ == "__main__":
    list_of_images = [p for p in BASE_IMAGE_DIR.glob("*.png") if p.with_suffix(".json").exists()]
    print(list_of_images)

    app = create_app(list_of_images)
    app.run_server(debug=True)
