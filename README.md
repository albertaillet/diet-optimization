## Diet optimization

# Notes

## Data sources

### Reference for products and prices

To get reference data on the food products that are chosen to be included, the following database can be used:

-   [Open food facts](https://world.openfoodfacts.org/), which is a collaborative project for reference of food products.
-   [Open food prices](https://prices.openfoodfacts.org/), which is an open crowdsourced database of food prices.

### Reference for food composition and micronutrients

-   [The Swiss Food Composition Database](https://valeursnutritives.ch/en/)
    Data collection of the Federal Food Safety and Veterinary Office FSVO on the composition of foods that are available
    in Switzerland. The version available at the time of writing (V6.5) contains information on 1,145 foodstuffs.
-   [The ANSES-CIQUAL French food composition table](https://ciqual.anses.fr/)
    The ANSES-CIQUAL food composition table gives information on the average nutritional composition of food consumed in France.
    67 components each for 100g of edible portion and an average value, a minimum and a maximum, together with a confidence code (A=very reliable, D=less reliable).
    The version available at the time of writing (version 2020) contains information on 3,185 food items.
-   [Livsmedelsdatabasen, The Swedish Food Composition Database](https://livsmedelsverket.se/livsmedel-och-innehall/naringsamne/livsmedelsdatabasen),
    which contains roughly 2,400 food items. For each food item, values ​​are given for over 50 nutrients.
-   [Fineli](https://fineli.fi/fineli/en/index).
    The national Food Composition Database in Finland, maintained by the Finnish Institute for Health and Welfare.
-   [Matvaretabellen, The Norwegian Food Product Table](https://matvaretabellen.no/en/search/) is a food database that
    shows the energy and nutrient content of foods, it contains nutrient content of more than the 2.000 most commonly
    eaten foods and recipes dishes in Norway.
-   [FoodData Central](https://fdc.nal.usda.gov/), USDA’s comprehensive source of food composition data with multiple distinct data types.

Here is the combined table listing the availability of different nutrients in the three databases:

| Nutrient \ Database       | Switzerland | France | Sweden |
| ------------------------- | ----------- | ------ | ------ |
| Energy value              | ✅          | ✅     | ✅     |
| Energy, calories          | ✅          | ✅     | ✅     |
| Energy, joules            | ✅          | ✅     | ✅     |
| Fat, total                | ✅          | ✅     | ✅     |
| Carbohydrates, available  | ✅          | ✅     | ✅     |
| Dietary fibres            | ✅          | ✅     | ✅     |
| Protein                   | ✅          | ✅     | ✅     |
| Salt (NaCl)               | ✅          | ✅     | ✅     |
| Alcohol                   | ✅          | ✅     | ✅     |
| Water                     | ✅          | ✅     | ✅     |
| Vitamin A activity, RE    | ✅          | ❌     | ❌     |
| Vitamin A activity, RAE   | ✅          | ❌     | ❌     |
| Retinol                   | ✅          | ✅     | ✅     |
| Beta-carotene activity    | ✅          | ❌     | ❌     |
| Beta-carotene             | ✅          | ✅     | ✅     |
| Vitamin B1 (thiamine)     | ✅          | ✅     | ✅     |
| Vitamin B2 (riboflavin)   | ✅          | ✅     | ✅     |
| Vitamin B6 (pyridoxine)   | ✅          | ✅     | ✅     |
| Vitamin B12 (cobalamin)   | ✅          | ✅     | ✅     |
| Niacin                    | ✅          | ✅     | ✅     |
| Folate                    | ✅          | ✅     | ✅     |
| Pantothenic acid          | ✅          | ✅     | ✅     |
| Vitamin C (ascorbic acid) | ✅          | ✅     | ✅     |
| Vitamin D (calciferol)    | ✅          | ✅     | ✅     |
| Vitamin E (α-tocopherol)  | ✅          | ✅     | ✅     |
| Vitamin K                 | ❌          | ✅     | ✅     |
| Potassium (K)             | ✅          | ✅     | ✅     |
| Sodium (Na)               | ✅          | ✅     | ✅     |
| Chloride (Cl)             | ✅          | ✅     | ❌     |
| Calcium (Ca)              | ✅          | ✅     | ✅     |
| Magnesium (Mg)            | ✅          | ✅     | ✅     |
| Phosphorus (P)            | ✅          | ✅     | ✅     |
| Iron (Fe)                 | ✅          | ✅     | ✅     |
| Iodide (I)                | ✅          | ✅     | ✅     |
| Zinc (Zn)                 | ✅          | ✅     | ✅     |
| Selenium (Se)             | ✅          | ✅     | ✅     |
| Fatty acids               | ✅          | ✅     | ✅     |
| FA saturated              | ✅          | ✅     | ✅     |
| FA monounsaturated        | ✅          | ✅     | ✅     |
| FA polyunsaturated        | ✅          | ✅     | ✅     |
| Cholesterol               | ✅          | ✅     | ✅     |
| Ash                       | ❌          | ✅     | ✅     |
| Sugars                    | ❌          | ✅     | ✅     |
| Organic acids             | ❌          | ✅     | ❌     |
| Polyols                   | ❌          | ✅     | ❌     |
| Retinol equivalents (RE)  | ❌          | ✅     | ✅     |
| Wholegrain total          | ❌          | ❌     | ✅     |
| Waste                     | ❌          | ❌     | ✅     |
