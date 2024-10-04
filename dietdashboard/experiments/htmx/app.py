from flask import Flask, render_template, render_template_string, request

app = Flask(__name__)


@app.route("/")
def index():
    currencies = ["USD", "EUR", "GBP"]
    sliders = [10, 20, 30]
    return render_template("index.html", currencies=currencies, sliders=sliders)


@app.route("/optimize", methods=["POST"])
def optimize():
    currency = request.form.get("currency", "USD")
    sliders = request.form.getlist("slider[]", type=float)

    # Perform simple optimization (for demonstration purposes)
    total = sum(sliders) * (1 if currency == "USD" else 0.85)

    # Return the updated result as HTML
    return render_template_string(
        """
        <h5>Total: {{ total | round(2) }} {{ currency }}</h5>
        <table>
            <tr><td>Item 1</td><td>{{ sliders[0] }}</td></tr>
            <tr><td>Item 2</td><td>{{ sliders[1] }}</td></tr>
        </table>
    """,
        total=total,
        currency=currency,
        sliders=sliders,
    )


if __name__ == "__main__":
    app.run(debug=True)
