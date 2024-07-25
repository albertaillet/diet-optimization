"""This script extracts the html tables in the fetched webpage with the Nordic Nutrition Recommendations 2023 to csv.

Usage of script DATA_DIR=<data directory> python scripts/recommendations_extract_tables.py
"""

import csv
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


def extract_text(td: BeautifulSoup) -> str:
    # Remove the <sup> tag and its contents, as they only contain footnotes (of format "1"; "5"; "5,6" or "1,2,6")
    sup_pattern = re.compile(r"^\d+(,\d+)*$")
    for sup in td.find_all("sup"):
        assert sup_pattern.match(sup.text), sup.text
        sup.extract()
    # Remove the <sub> tag but keep its contents, as they contain vital info like Vitamin B<sub>12</sub>
    for sub in td.find_all("sub"):
        assert sub.text.isdigit() or sub.text == "µg", sub.text  # noqa: RUF001
        sub.unwrap()
    assert len(td.find_all("sub")) == 0
    return td.get_text(separator="", strip=True)


def extract_table(table: BeautifulSoup, file):
    writer = csv.writer(file)
    for tr in table.find_all("tr"):
        writer.writerow([extract_text(td) for td in tr.find_all("td")])


if __name__ == "__main__":
    with (DATA_DIR / "recommendations.html").open("r") as file:
        content = file.read()
    soup = BeautifulSoup(content, "html.parser")

    (DATA_DIR / "recommendations").mkdir(exist_ok=True)

    for i, table in enumerate(soup.find_all("tbody")):
        with (DATA_DIR / f"recommendations/table_{i}.csv").open("w") as file:
            extract_table(table, file)
