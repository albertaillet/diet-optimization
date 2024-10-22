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
temporary_csv_data: list[tuple[int, dict[str, str]]] = []

# Define columns with details such as name, editability, and input type
columns = [
    {"name": "ID", "editable": False, "type": "text"},
    {"name": "Name", "editable": True, "type": "text"},
    {"name": "Date", "editable": True, "type": "date"},
    {"name": "Amount (g)", "editable": True, "type": "number"},
    {"name": "Calories", "editable": False, "type": "number"},
    {"name": "Fat (g)", "editable": False, "type": "number"},
    {"name": "Carbs (g)", "editable": False, "type": "number"},
    {"name": "Protein (g)", "editable": False, "type": "number"},
]


@app.route("/", methods=["GET"])
def index():
    global temporary_csv_data
    if not temporary_csv_data:
        # Load initial CSV data from disk if temporary data is not present
        csv_path = DATA_DIR / "example.csv"
        temporary_csv_data = read_csv_file(csv_path)
    return render_template("index.html", csv_data=temporary_csv_data, columns=columns)


@app.route("/update_row/<int:row_index>", methods=["POST"])
def update_row(row_index: int):
    global temporary_csv_data
    if row_index < len(temporary_csv_data):
        # Update the specific row with form data
        updated_row = request.form.to_dict()
        temporary_csv_data[row_index] = (row_index, updated_row)
    return redirect(url_for("index"))


def read_csv_file(filepath: Path) -> list[tuple[int, dict[str, str]]]:
    # Reads a CSV file and returns the data as a list of dictionaries
    with filepath.open(newline="", encoding="utf-8") as file:
        return list(enumerate(csv.DictReader(file)))


if __name__ == "__main__":
    app.run(debug=True)
