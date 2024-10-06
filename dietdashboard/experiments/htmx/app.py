from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List
from pathlib import Path
import uvicorn

# Setting up the FastAPI app and Jinja2 templates


POSSIBLE_CURRENCIES = ["EUR", "CHF"]


def create_app() -> FastAPI:
    templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")

    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        sliders = [
            {
                "name": f"NutrientName{i}",
                "id": f"nutrient_{i}",
                "min": 0,
                "max": 100,
                "lower": 10,
                "upper": 45,
            }
            for i in range(5)
        ]
        macronutrients = ["Protein", "Carbohydrates", "Fats"]
        micronutrients = ["Vitamin A", "Vitamin C", "Iron", "Calcium"]
        context = dict(
            currencies=POSSIBLE_CURRENCIES,
            sliders=sliders,
            macronutrients=macronutrients,
            micronutrients=micronutrients,
            request=request,
        )
        return templates.TemplateResponse("index.html", context)

    @app.post("/optimize", response_class=HTMLResponse)
    async def optimize(request: Request):
        form_data = await request.form()
        import code

        code.interact(local=locals())
        form_data_dict = {key: value for key, value in zip(request.query_params.keys(), form_data)}
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "form_data": form_data_dict,
            },
        )

    return app


app = create_app()
if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)
