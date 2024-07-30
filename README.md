# Diet optimization

## Installation

From the root of the repository run

```bash
pip install -e ".[dev]"
```

## Usage

To fetch everything use:

```
make all
```

Else the individual make commands can be used.

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

### Data source for nutrition recommendations

[Nordic Nutrition Recommendations 2023](https://pub.norden.org/nord2023-003/recommendations.html), which contains the following for a select number of nurtients.

| Term                                             | Definition                                                                                                                                                                                                              |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Average Requirement (AR)**                     | The average daily nutrient intake level estimated to meet the requirements of half of the individuals in a particular life-stage group in the general population. Used to assess adequacy of nutrient intake of groups. |
| **Recommended Intake (RI)**                      | The average daily dietary nutrient intake level sufficient to meet the nutrient requirements of nearly all (97.5%) individuals in a life-stage group. Used to plan diets for individuals and groups.                    |
| **Adequate Intake (AI)**                         | The recommended average daily intake level based on observed or experimentally determined estimates of nutrient intake by a group. Used when an RI cannot be determined.                                                |
| **Provisional AR**                               | The average daily nutrient intake level suggested to meet the requirements of half of the individuals in a life-stage group. An approximation of AR with larger uncertainty.                                            |
| **Recommended intake range of macronutrients**   | The recommended average daily nutrient range of energy-providing macronutrients expressed as a percentage of total energy intake. Associated with reduced risk of chronic diseases.                                     |
| **Tolerable Upper Intake Level (UL)**            | The highest average daily nutrient intake level likely to pose no risk of adverse health effects to almost all individuals.                                                                                             |
| **Chronic Disease Risk Reduction Intake (CDRR)** | The intake level above which reduction is expected to reduce chronic disease risk within life-stage groups in the general population.                                                                                   |

## Optimization library

For optimizing the diet, a linear programming python library is used, here are the considered choices:

-   **SciPy (`scipy.optimize.linprog`)**

    -   [Repository](https://github.com/scipy/scipy)
    -   [Documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html)

-   **OR-Tools (`ortools.linear_solver`)**

    -   [Repository](https://github.com/google/or-tools)
    -   [Documentation](https://or-tools.github.io/docs/pdoc/ortools/linear_solver.html)
    -   [Example](https://github.com/google/or-tools/blob/stable/examples/python/linear_programming.py)
    -   [Usage in OFF](https://github.com/openfoodfacts/recipe-estimator/blob/main/recipe_estimator.py)

-   **CVXPY**

    -   [Repository](https://github.com/cvxpy/cvxpy)

-   **PuLP**

    -   [Repository](https://github.com/coin-or/pulp)

-   **Pyomo**

    -   [Repository](https://github.com/Pyomo/pyomo)

-   **Cvxopt**

    -   [Repository](https://github.com/cvxopt/cvxopt)

-   **GLPK (GNU Linear Programming Kit)**

    -   [Repository](https://www.gnu.org/software/glpk/)

-   **Cbc**

    -   [Repository](https://github.com/coin-or/Cbc)

-   **Gurobi**
    -   [Gurobi Website](https://www.gurobi.com/)
    -   Note: Gurobi is commercial software
