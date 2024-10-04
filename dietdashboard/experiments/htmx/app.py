from flask import Flask, render_template, render_template_string, request

POSSIBLE_CURRENCIES = ["EUR", "CHF"]


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        sliders = [None] * 5
        macronutrients = ["Protein", "Carbohydrates", "Fats"]
        micronutrients = ["Vitamin A", "Vitamin C", "Iron", "Calcium"]
        return render_template(
            "index.html",
            currencies=POSSIBLE_CURRENCIES,
            sliders=sliders,
            macronutrients=macronutrients,
            micronutrients=micronutrients,
        )

    @app.route("/optimize", methods=["POST"])
    def optimize():
        form_data = request.form.to_dict(flat=False)
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
    app = create_app()
    app.run(debug=True)
