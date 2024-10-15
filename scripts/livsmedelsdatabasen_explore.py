# %%
"""This script reads the downloaded Livsmedelsverkets livsmedelsdatabas.

Usage of script DATA_DIR=<path to data directory> python livsmedelsdatabasen_fetch.py
https://soknaringsinnehall.livsmedelsverket.se
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"

# Drop two first rows
livsmedels_db = pd.read_excel(DATA_DIR / "LivsmedelsDB_2024_05_29.xlsx", skiprows=2)
# livsmedels_db.to_csv(DATA_DIR / "LivsmedelsDB_2024_05_29.csv", index=False)

# %%
id_cols = [
    "Livsmedelsnamn",
    "Livsmedelsnummer",
    "Gruppering",
]
per_100g_cols = [
    "Energi (kcal)",
    "Energi (kJ)",
    "Fett, totalt (g)",
    "Protein (g)",
    "Kolhydrater, tillgängliga (g)",
    "Fibrer (g)",
    "Vatten (g)",
    "Alkohol (g)",
    "Aska (g)",
    "Sockerarter, totalt (g)",
    "Monosackarider (g)",
    "Disackarider (g)",
    "Tillsatt socker (g)",
    "Fritt socker (g)",
    "Fullkorn totalt (g)",
    "Summa mättade fettsyror (g)",
    "Fettsyra 4:0-10:0 (g)",
    "Laurinsyra C12:0 (g)",
    "Myristinsyra C14:0 (g)",
    "Palmitinsyra C16:0 (g)",
    "Stearinsyra C18:0 (g)",
    "Arakidinsyra C20:0 (g)",
    "Summa enkelomättade fettsyror (g)",
    "Palmitoljesyra C16:1 (g)",
    "Oljesyra C18:1 (g)",
    "Summa fleromättade fettsyror (g)",
    "Linolsyra C18:2 (g)",
    "Linolensyra C18:3 (g)",
    "Arakidonsyra C20:4 (g)",
    "EPA (C20:5) (g)",
    "DPA (C22:5) (g)",
    "DHA (C22:6) (g)",
    "Kolesterol (mg)",
    "Vitamin A (RE/µg)",
    "Retinol (µg)",
    "Betakaroten/β-Karoten (µg)",
    "Vitamin D (µg)",
    "Vitamin E (mg)",
    "Vitamin K (µg)",
    "Tiamin (mg)",
    "Riboflavin (mg)",
    "Niacin (mg)",
    "Niacinekvivalenter (NE/mg)",
    "Vitamin B6 (mg)",
    "Folat, totalt (µg)",
    "Vitamin B12 (µg)",
    "Vitamin C (mg)",
    "Fosfor, P (mg)",
    "Jod, I (µg)",
    "Järn, Fe (mg)",
    "Kalcium, Ca (mg)",
    "Kalium, K (mg)",
    "Magnesium, Mg (mg)",
    "Natrium, Na (mg)",
    "Salt, NaCl (g)",
    "Selen, Se (µg)",
    "Zink, Zn (mg)",
    "Avfall (skal etc.) (%)",
]

# %% Create a DataFrame with example of food eaten in a day:
columns = ["Mat", "Mängd (g)", "Livsmedelsnummer"]
data = [
    ["kikärtor", 250, 3815],
    ["tofu", 350, 905],
    ["brysselkål", 250, 5863],
    ["olivolja", 50, 35],
    ["sojasås", 8, 909],
    ["jordnötssmör", 30, 1559],
    ["havregryn", 25, 702],
    ["tofu", 250, 905],
    ["kikärtor", 150, 3815],
    ["lax", 80, 1316],
    ["olivolja", 15, 35],
    ["sojasås", 3, 909],
    ["havregryn", 30, 702],
    ["jordnötssmör", 30, 1559],
    ["vatten", 1600, 1953],
]
diet = pd.DataFrame(data, columns=columns)

# %% Match the food with the Livsmedelsverket database using a merge
diet_nutrients = diet.merge(
    livsmedels_db[id_cols + per_100g_cols],
    how="left",
    left_on="Livsmedelsnummer",
    right_on="Livsmedelsnummer",
)

# %% Make a table that shows the nutrients in the diet by mutiplying
# amount with the values that are per 100g
# Multiply the amount with the values that are per 100g
diet_nutrients_calculated = diet_nutrients.copy()
for col in per_100g_cols:
    diet_nutrients_calculated[col] = (diet_nutrients[col] * diet_nutrients["Mängd (g)"] / 100).round(2)

# %% Make a final row that sums the nutrients
diet_nutrients_sum = diet_nutrients_calculated[["Mängd (g)", *per_100g_cols]].sum().round(2)

# %% Append the sum to the DataFrame
diet_nutrients_sum["Mat"] = "Summa"
diet_nutrients_sum["Livsmedelsnamn"] = "Summa"
diet_nutrients_final = pd.concat([diet_nutrients_calculated, diet_nutrients_sum.to_frame().T])

# %% Save the DataFrame to a csv file
print_cols = [
    "Livsmedelsnamn",
    "Mängd (g)",
    "Energi (kcal)",
    "Fett, totalt (g)",
    "Protein (g)",
    "Kolhydrater, tillgängliga (g)",
    "Fibrer (g)",
    "Vatten (g)",
    # "Alkohol (g)",
    # "Aska (g)",
    "Sockerarter, totalt (g)",
    # "Monosackarider (g)",
    # "Disackarider (g)",
    "Tillsatt socker (g)",
    # "Fritt socker (g)",
    # "Fullkorn totalt (g)",
    "Summa mättade fettsyror (g)",
    # "Fettsyra 4:0-10:0 (g)",
    # "Laurinsyra C12:0 (g)",
    # "Myristinsyra C14:0 (g)",
    # "Palmitinsyra C16:0 (g)",
    # "Stearinsyra C18:0 (g)",
    # "Arakidinsyra C20:0 (g)",
    "Summa enkelomättade fettsyror (g)",
    # "Palmitoljesyra C16:1 (g)",
    # "Oljesyra C18:1 (g)",
    "Summa fleromättade fettsyror (g)",
    # "Linolsyra C18:2 (g)",
    # "Linolensyra C18:3 (g)",
    # "Arakidonsyra C20:4 (g)",
    # "EPA (C20:5) (g)",
    # "DPA (C22:5) (g)",
    # "DHA (C22:6) (g)",
    "Kolesterol (mg)",
    "Vitamin A (RE/µg)",
    "Retinol (µg)",
    "Betakaroten/β-Karoten (µg)",
    "Vitamin D (µg)",
    "Vitamin E (mg)",
    "Vitamin K (µg)",
    "Tiamin (mg)",
    "Riboflavin (mg)",
    "Niacin (mg)",
    "Niacinekvivalenter (NE/mg)",
    "Vitamin B6 (mg)",
    # "Folat, totalt (µg)",
    "Vitamin B12 (µg)",
    "Vitamin C (mg)",
    # "Fosfor, P (mg)",
    # "Jod, I (µg)",
    "Järn, Fe (mg)",
    "Kalcium, Ca (mg)",
    # "Kalium, K (mg)",
    "Magnesium, Mg (mg)",
    # "Natrium, Na (mg)",
    "Salt, NaCl (g)",
    # "Selen, Se (µg)",
    # "Zink, Zn (mg)",
    # "Avfall (skal etc.) (%)",
]

diet_nutrients_final[print_cols].to_csv(DATA_DIR / "diet_nutrients.csv", index=False)

# %%
latex_string = diet_nutrients_final[print_cols].to_latex(
    index=False,
    float_format="%.2f",
)
print(latex_string)
# %%
diet_nutrients_sum[print_cols]
# %%
check = "Vitamin C (mg)"  # "Järn, Fe (mg)"
diet_nutrients_final[["Livsmedelsnamn", check]].sort_values(check, ascending=False)
# %%
print_cols = [
    "Livsmedelsnamn",
    "Mängd (g)",
    "Energi (kcal)",
    "Fett, totalt (g)",
    "Summa mättade fettsyror (g)",
    "Summa enkelomättade fettsyror (g)",
    "Summa fleromättade fettsyror (g)",
    "Kolhydrater, tillgängliga (g)",
    "Sockerarter, totalt (g)",
    "Fibrer (g)",
    "Protein (g)",
    # "Vatten (g)",
]
diet_nutrients_final[print_cols].round(1)

# %%
