# Notes

## General Notes

-   In dashboard, have a choice to also include micronutrients and a choice to only use the reported values
-   Should have some kind of data validation of prices and nutrients, to not have any erroneous outliers.

## Notes about Open Food Facts entries

-   Filets de colin d'alaska 1 kg (2100/02987) (code: 3250392130091) ingredients_text also includes things that are not ingredients.
-   Ybarra olive oil (code: 8410086990607) is not complete.

## Notes about optimization

-   Would be nice to be able to also minimize certain nutrients with some sort of hyperparameter.
    For example saturated fat or carbs at the same time as price.

## Notes about nutrition estimation

The nutrition estimation of OFF is located here.

https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionCiqual.pm

https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionEstimation.pm

The consulted repository version is available using the same URL, but replacing main with the permalink:
main -> ab5c4410cd0f3017803cdfe4304f91dfa7636034

TODO: When using off exports, remove the following scripts:
- scripts/ciqual_fetch.py
- scripts/comparison_app.py
- scripts/livsmedelsdatabasen_explore.py
- scripts/locations_summarize.py
- scripts/make_ciqual_summary.py
- scripts/prices_fetch.py
- scripts/products_fetch.py
- scripts/products_summarize.py
