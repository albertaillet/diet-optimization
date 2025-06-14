#!/usr/bin/env -S uv run --extra plotting
"""Compare the ALIM_CODE values in the data sets based on ciqual codes (ciqual vs calnut vs agribalyse)."""

# %%
import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = Path(__file__).parent.parent / "data"
CIQUAL_CSV = DATA_DIR / "ciqual2020/alim.csv"
CALNUT_0_CSV = DATA_DIR / "calnut.0.csv"
CALNUT_1_CSV = DATA_DIR / "calnut.1.csv"
AGRIBALYSE_CSV = DATA_DIR / "agribalyse_synthese.csv"

ciqual = {row["alim_code"] for row in csv.DictReader(CIQUAL_CSV.open())}
calnut0 = {row["alim_code"] for row in csv.DictReader(CALNUT_0_CSV.open())}
calnut1 = {row["ALIM_CODE"] for row in csv.DictReader(CALNUT_1_CSV.open())}
agribalyse = {row["Code CIQUAL"] for row in csv.DictReader(AGRIBALYSE_CSV.open())}

assert calnut0 == calnut1, "calnut.0 and calnut.1 differ!"

# %%
from matplotlib import pyplot as plt  # noqa: E402
from matplotlib_set_diagrams import EulerDiagram  # noqa: E402

subsets = (ciqual, calnut1, agribalyse)
set_labels = ("ciqual", "calnut", "agribalyse")

# From https://agribalyse.ademe.fr/static/media/logo.e3e348f6.png
a_colors = ("#e9b312", "#618341", "#e3451d")
set_colors = (a_colors[2], "#6f92c0", a_colors[1])

cost = "simple"  # simple, logarithmic, relative
euler = EulerDiagram.from_sets(subsets, set_labels=set_labels, cost_function_objective=cost, set_colors=set_colors)
for subset_artist in euler.subset_label_artists.values():
    subset_artist.set_color("black")
plt.savefig(SCRIPT_DIR / "alim_euler.svg", bbox_inches="tight")

# Summary:
# +-----+-----+-----+------+
# | Ciq | Cal | Agr |  Num |
# +-----+-----+-----+------+
# |  X  |     |     |  358 |  Only in Ciqual
# |     |  X  |     |   24 |  Only in Calnut
# |     |     |  X  |    5 |  Only in Agribalyse
# |  X  |  X  |     |  407 |  In Ciqual and Calnut but not Agribalyse
# |  X  |     |  X  |  732 |  In Agribalyse and Ciqual but not Calnut
# |     |  X  |  X  |    0 |  In Agribalyse and Calnut but not Ciqual
# |  X  |  X  |  X  | 1688 |  In all three
# +-----+-----+-----+------+

# %%
only_in_agribalyse = agribalyse - ciqual - calnut1
print(f"Only in Agribalyse ({len(only_in_agribalyse)}):")
for row in csv.DictReader(AGRIBALYSE_CSV.open()):
    if row["Code CIQUAL"] in only_in_agribalyse:
        print(row["Code CIQUAL"], row["LCI Name"])

# %%
only_in_calnut = calnut1 - ciqual - agribalyse
print(f"\nOnly in Calnut ({len(only_in_calnut)}):")
for row in csv.DictReader(CALNUT_0_CSV.open()):
    if row["HYPOTH"] != "MB":
        continue  # To get unique ALIM_CODE values
    if row["alim_code"] in only_in_calnut:
        print(row["alim_code"], row["FOOD_LABEL"])
