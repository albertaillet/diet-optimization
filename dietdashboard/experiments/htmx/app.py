from flask import Flask, render_template, render_template_string, request

app = Flask(__name__)


@app.route("/")
def index():
    currencies = ["USD", "EUR", "GBP"]
    sliders = [10, 20, 30]
    macronutrients = ["Protein", "Carbohydrates", "Fats"]
    micronutrients = ["Vitamin A", "Vitamin C", "Iron", "Calcium"]
    return render_template(
        "index.html",
        currencies=currencies,
        sliders=sliders,
        macronutrients=macronutrients,
        micronutrients=micronutrients,
    )


@app.route("/optimize", methods=["POST"])
def optimize():
    currency = request.form.get("currency", "USD")
    sliders = request.form.getlist("slider[]", type=float)
    selected_macronutrients = request.form.getlist("macronutrients")
    selected_micronutrients = request.form.getlist("micronutrients")

    # Perform simple optimization (for demonstration purposes)
    total = sum(sliders) * (1 if currency == "USD" else 0.85)

    # Generate result content based on selected nutrients
    nutrient_summary = "<h5>Selected Macronutrients: {}</h5>".format(", ".join(selected_macronutrients))
    nutrient_summary += "<h5>Selected Micronutrients: {}</h5>".format(", ".join(selected_micronutrients))

    # Return the updated result as HTML
    return render_template_string(
        """
        <h5>Total: {{ total | round(2) }} {{ currency }}</h5>
        <table>
            <tr><td>Item 1</td><td>{{ sliders[0] }}</td></tr>
            <tr><td>Item 2</td><td>{{ sliders[1] }}</td></tr>
        </table>
        {{ nutrient_summary | safe }}
    """,
        total=total,
        currency=currency,
        sliders=sliders,
        nutrient_summary=nutrient_summary,
    )


if __name__ == "__main__":
    app.run(debug=True)
