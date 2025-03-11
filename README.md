# Diet optimization

This repository contains the code for some diet optimization projects. The goal is to create a tool for me to automatically generate a diet plan that meets set nutritional needs, while minimizing the cost, the environmental impact and the complexity of the diet.

## Prerequisites

General utilities and for running the backend:
-   `make` for running the commands in the `Makefile`.
-   `wget` for downloading the data.
-   `unzip` for extracting the data.
-   `uv` for running python scripts.
-   `duckdb` for the duckdb CLI.

To run the frontend:
-   `esbuild` for building the frontend.
-   `pnpm` for managing the frontend dependencies.

On Ubuntu, you can install some of these with:

```bash
sudo apt install make wget unzip
curl -fsSL https://install.duckdb.org | sh
curl -fsSL https://astral.sh/uv/install.sh | sh
curl -fsSL https://esbuild.github.io/dl/latest | sh
curl -fsSL https://get.pnpm.io/install.sh | sh
```

On MacOS they can be installed with `brew`:

```bash
brew install make wget unzip duckdb uv esbuild pnpm
```

## Usage

To run different parts of the project, check out the `Makefile` for the available commands.

## Data sources

### Reference for products and prices

To get reference data on the food products that are chosen to be included, the following database can be used:

-   [Open food facts](https://world.openfoodfacts.org/), which is a collaborative project for reference of food products.
-   [Open food prices](https://prices.openfoodfacts.org/), which is an open crowdsourced database of food prices.

### Reference for food composition and micronutrients

-   [The Swiss Food Composition Database](https://valeursnutritives.ch/en/)
    Data collection of the Federal Food Safety and Veterinary Office FSVO on the composition of foods that are available in Switzerland. The version available at the time of writing (V6.5) contains information on 1,145 foodstuffs.
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
-   [Nutrition Coordinating Center Food & Nutrient Database](https://www.ncc.umn.edu/food-and-nutrient-database/), curated by the University of Minnesota. Very comprehensive, but not free.

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

[Nordic Nutrition Recommendations 2023](https://pub.norden.org/nord2023-003/recommendations.html) (NNR2023), which contains the following for a select number of nurtients.

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

-   **SciPy (`scipy.optimize.linprog`)**: [Repository](https://github.com/scipy/scipy), [Documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html)

-   **highspy** (python wrapper for the HiGHS solver): [Repository](https://github.com/ERGO-Code/HiGHS) [Pipy](https://pypi.org/project/highspy/)

-   **OR-Tools (`ortools.linear_solver`)**: [Repository](https://github.com/google/or-tools), [Documentation](https://or-tools.github.io/docs/pdoc/ortools/linear_solver.html), [Example](https://github.com/google/or-tools/blob/stable/examples/python/linear_programming.py), [Usage in OFF](https://github.com/openfoodfacts/recipe-estimator/blob/main/recipe_estimator.py)

-   **CVXPY** (python modeling language for multiple sovlers): [Repository](https://github.com/cvxpy/cvxpy)

-   **PuLP**: [Repository](https://github.com/coin-or/pulp)

-   **Pyomo**: [Repository](https://github.com/Pyomo/pyomo), [Diet optimization example](https://github.com/Pyomo/PyomoGallery/tree/0b809937cfb9c53a78bc108328a88401685d22bd/diet)

-   **Cvxopt**: [Repository](https://github.com/cvxopt/cvxopt)

-   **GLPK (GNU Linear Programming Kit)**: [Repository](https://www.gnu.org/software/glpk/)

-   **Cbc**: [Repository](https://github.com/coin-or/Cbc)

-   **Gurobi**: [Gurobi Website](https://www.gurobi.com/), Note: Gurobi is commercial software

A table with different solvers is available here:
[cvxpy.org](https://www.cvxpy.org/tutorial/solvers/index.html#choosing-a-solver)

### Other nutrient tackers:

Open source:

-   [awesome-nutrition-tracking](https://github.com/jrhizor/awesome-nutrition-tracking)
-   [OpenNutriTracker](https://github.com/simonoppowa/OpenNutriTracker) (iOS / Android)
-   [waistline](https://github.com/davidhealey/waistline) (Android)
-   🎖️[Energize](https://codeberg.org/epinez/Energize/) (Android)
    -   TODO: checkout this tool to extract the Swiss Food Composition Database [update_sfcd_data.py](https://codeberg.org/epinez/Energize/src/branch/main/scripts/update_sfcd_data/update_sfcd_data.py)

Personal projects:
-   🎖️[kale.world](https://kale.world/) (Found on [Hacker News](https://news.ycombinator.com/item?id=22689346))

### Proprietary nutrition trackers and databases:

Apps with API, database documentation, licensing or search tools:

-   [Edamam](https://www.edamam.com/), has an [API](https://developer.edamam.com/food-database-api-docs) and database licensing.
-   [Calorie Counter by FatSecret](https://www.fatsecret.com/), has an [API](https://blog.fatsecret.com/).
-   [Nutritionix](https://www.nutritionix.com/), has an [API](https://www.nutritionix.com/business/api) and [database](https://www.nutritionix.com/database) documentation for nutrition data.
-   [Chomp](https://www.chompthis.com/), has an API.
-   [Spoonacular](https://spoonacular.com/), has an API.
-   [MyNetDiary](https://www.mynetdiary.com/), has an API and [database licensing](https://www.mynetdiary.com/food-database.html).
-   [Lose It!](https://www.loseit.com/), has an [API](https://www.loseit.com/api/).
-   [DietaGram](http://dietagram.com/), has an [API](http://dietagram.com/api-page).
-   [ESHA Nutrition Database](https://esha.com/), has an [API](https://esha.com/products/nutrition-database-api/) and [Database Licensing](https://esha.com/products/database-licensing/).
-   [Yazio](https://www.yazio.com/), has a [search tool](https://www.yazio.com/en/foods) and apparently and [API](https://github.com/saganos/yazio_public_api).
-   [Eat This Much](https://www.eatthismuch.com/), they have a database exploration tools at this [link](https://www.eatthismuch.com/food/browse/).
-   [MyFoodDiary](https://www.myfooddiary.com/), search in database available [here](https://www.myfooddiary.com/foods).
-   🎖️[Nutrition value](https://www.nutritionvalue.org/), is a php website using the USDA database, a user has created and API for it [here](https://github.com/ryojp/nutrition-api).
-   [Samsung Food Recipe Nutrition Calculator](https://samsungfood.com/recipe-nutrition-calculator/), nutrition calculator for recipes.
-   🎖️[TheMealDB](https://www.themealdb.com/), small meal and recipe database and API.
-   [GroceryDB](https://github.com/Barabasi-Lab/GroceryDB)

Apps with a bit of information about their databases:

-   [Cronometer](https://cronometer.com/), data sources described [here](https://support.cronometer.com/hc/en-us/articles/360018239472-Data-Sources).
-   [Lifesum](https://lifesum.com/), data sources described [here](https://lifesum.helpshift.com/hc/en/3-lifesum/faq/48-lifesum-s-food-database/).
-   [Noom](https://www.noom.com/), data sources described [here](https://www.noom.com/blog/inside-look-nooms-food-database/).
-   [MyFoodData](https://www.myfooddata.com/), data sources described [here](https://www.myfooddata.com/about-the-data).
-   [MyNetDiary](https://www.mynetdiary.com/food-database.html), data sources described [here](https://www.mynetdiary.com/food-database.html).

Other apps:

-   [Joy Health Tracker](https://www.joyapp.com/)
-   [MyFitnessPal](https://www.myfitnesspal.com/)
-   [MyPlate](https://www.myplate.gov/resources/tools/startsimple-myplate-app), USDA's nutrition tracker.
-   [iEatBetter](https://www.ieatbetter.com/)
-   [Mealime](https://www.mealime.com/)
-   [PlateJoy](https://www.platejoy.com/)
-   [EatLove](https://www.eatlove.is/)
-   [MacroFactor](https://macrofactorapp.com/)
-   [Rex](https://www.rex.fit/), calorie and exercise tracking over WhatsApp, has some kind of API.
-   [Lolo](https://apps.apple.com/us/app/lolo-ai-food-calorie-tracker/id6448986851?l=en)
-   [SnackFolio](https://www.snackfolio.com/), offline friendly nutrition tracker.
-   [Cali AI](https://www.calai.app), calorie tracking app with a focus on tracking food portions from images using multimodal AI.
-   [Truefood.tech](https://truefood.tech/), from a team of researchers to find least processed food.
-   [Foodop](https://foodop.dk), a Danish web app to optimize kitchen operations.

Other tools:
-   [Terra](https://tryterra.co/) is a Health API for Wearable and Sensor Data that integrates with nutrition trackers.
-   [BigOven](https://www.bigoven.com/) is a recipe database.
-   [SnapCalorie](https://www.snapcalorie.com/), is an [API](https://snapcalorie.github.io/) for taking a picture of a food item and getting the nutritional information.
-   [Foodvisor](https://www.foodvisor.io/en/), they have an API for their food recognition tool.
-   NanEye, WIP project connecting biomarkers to nutrition data.
-   [Completefoods](https://www.completefoods.co/), prev diy soylent, a database of recipes for diy meal replacement shakes.


### Food classification standards:
Related [xkcd](https://xkcd.com/927/).

-   [Open Food Facts Taxonomy](https://world.openfoodfacts.org/taxonomy), a taxonomy for food products, [wiki](https://wiki.openfoodfacts.org/Global_taxonomies).
-   [LanguaL](https://www.langual.org/default.asp), an international framework for food description.
-   [FoodEx2](https://www.efsa.europa.eu/en/data/data-standardisation), a food classification standardisation system.
-   [FoodOn](https://foodon.org/), an ontology for food [github](https://github.com/FoodOntology/foodon). Available in [Ontobee](https://ontobee.org/ontology/FOODON).

### Other links

Random links:
-   [Open Food Facts post on HN](https://news.ycombinator.com/item?id=22683416)
-   [Food Facts](https://www.foodfacts.se/), Swedish food stratup at Norrsken House.
-   [Random kaggle dataset](https://www.kaggle.com/datasets/trolukovich/nutritional-values-for-common-foods-and-products), nutritional values for common foods and products, source unclear.
-   [Nutrition5k](https://github.com/google-research-datasets/Nutrition5k), a dataset of 5k images of food items with nutritional information.
-   [Documenu](https://github.com/documenu), Restaurant menu API.
-   [Foodoptimizer](https://kkloste.github.io/projects/foodoptimizer/), a blogpost on food optimization.
-   🎖️[knowledge-mining-nutrition](https://forgemia.inra.fr/stephane.dervaux/knowledge-mining-nutrition) Ongoing research project on knowledge mining in nutrition (02/2025).
-   [PyomoDietProblem](https://github.com/Pyomo/PyomoGallery/blob/main/diet/DietProblem.ipynb), a Pyomo example for the diet problem.


Outdated projects:
-   [MyDietCoach](https://www.mydietcoachapp.com/) (deprecated, now redirects to [Bending Spoons](https://www.bendingspoons.com/))
-   [EuroFIR](https://www.eurofir.org/), a European network that provides a comprehensive food composition database. The project has ended, so support and database updates is questionable (https://www.eurofir.org/foodexplorer). It also seems to use Wordpress.
-   [Optifood](https://www.sciencedirect.com/science/article/pii/S0002916523049262) A paper about the use of linear programming to determine if a food product can ensure adequate nutrients for Cambodian infants.
-   [Nutrioptimizer](https://nutrioptimizer.com) indian website for diet optimization, by Sri Mookambika Infosystems, apparently only runs on Mozilla Firefox Browser.
