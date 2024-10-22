"""
app.py

A Flask web application that reads a CSV file, displays it in an editable table using Jinja2 templates,
and allows users to modify the data temporarily in memory. The original CSV file is not modified.

Environment Variables:
    DATA_DIR: Path to the directory containing the CSV file 'nutrient_map.csv'.
"""

import csv
import os
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

# Define the data directory using environment variable
DATA_DIR = Path(os.getenv("DATA_DIR", ""))

# Store the temporary CSV data in memory
temporary_csv_data: list[dict[str, str]] = []


# Route to read CSV file from disk and render it in editable format
@app.route("/", methods=["GET", "POST"])
def index():
    global temporary_csv_data
    if not temporary_csv_data:
        # Load initial CSV data from disk if temporary data is not present
        csv_path = DATA_DIR / "nutrient_map.csv"
        temporary_csv_data = read_csv_file(csv_path)

    if request.method == "POST":
        # Update temporary CSV data with form inputs
        updated_data = request.form.to_dict(flat=False)
        temporary_csv_data = convert_form_data_to_dict(updated_data)
        return redirect(url_for("index"))

    return render_template("index.html", csv_data=list(enumerate(temporary_csv_data)))


def read_csv_file(filepath: Path) -> list[dict[str, str]]:
    # Reads a CSV file and returns the data as a list of dictionaries
    with filepath.open(newline="", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        return list(csv_reader)


def convert_form_data_to_dict(form_data: dict[str, list[str]]) -> list[dict[str, str]]:
    # Converts form data to a list of dictionaries (rows)
    fieldnames = form_data.keys()
    rows = zip(*form_data.values(), strict=True)
    return [dict(zip(fieldnames, row, strict=True)) for row in rows]


if __name__ == "__main__":
    app.run(debug=True)
