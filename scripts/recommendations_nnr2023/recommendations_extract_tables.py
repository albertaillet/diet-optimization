"""This script extracts the html tables in the fetched webpage with the Nordic Nutrition Recommendations 2023 to csv."""

import csv
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

# Key: number of table in scraped html file
# Value: goal filename and Table title in the Nordic Nutrition Recommendations 2023.
TABLES = {
    8: ("protein_AR_and_RI", "Table 11 Average requirements and recommended intakes of protein by life stage"),
    9: ("vitamins_RI", "Table 12 Recommended intake for vitamins"),
    10: ("vitamins_AI", "Table 13 Adequate intake for vitamins"),
    11: ("minerals_RI", "Table 14 Recommended intake for minerals"),
    12: ("minerals_AI", "Table 15 Adequate intake for minerals"),
    13: ("sodium_RI", "Table 16 Chronic disease risk reduction intake  of sodium."),
    14: ("vitamins_AR", "Table 17 Average requirements of vitamins."),
    15: ("vitamins_PAR", "Table 18 Provisional average requirements of vitamins."),
    16: ("minerals_AR", "Table 19 Average requirements of minerals."),
    17: ("minerals_PAR", "Table 20 Provisional average requirements of minerals."),
    18: ("levels_upper_intake", "Table 21 Tolerable upper intake levels of vitamins and minerals for adults."),
    19: ("levels_comparison_summary", "Table 22 Comparison between RI and AI set by NNR2023 and NNR2012."),
}


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
        writer.writerow([extract_text(td) for td in tr.find_all(["td", "th"])])


if __name__ == "__main__":
    with (DATA_DIR / "recommendations_nnr2023.html").open("r") as file:
        content = file.read()
    soup = BeautifulSoup(content, "html.parser")

    (DATA_DIR / "recommendations_nnr2023").mkdir(exist_ok=True)

    for i, table in enumerate(soup.find_all("tbody")):
        if i not in TABLES:
            continue
        filename, title = TABLES[i]
        with (DATA_DIR / f"recommendations_nnr2023/{filename}.csv").open("w") as file:
            extract_table(table, file)
