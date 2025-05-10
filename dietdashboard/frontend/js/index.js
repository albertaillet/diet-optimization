import { registerCheckBoxes } from "./components/checkboxes";
import { registerCurrencySelect } from "./components/currency";
import { Locations } from "./components/locations";
import { Result } from "./components/result";
import { Sliders } from "./components/sliders";
import { autoType, csv, csvParse } from "./d3";
import { effect, reactive } from "./reactivity";

export const persistState = state => localStorage.setItem("state", JSON.stringify(state));
const restoreState = () => JSON.parse(localStorage.getItem("state"));

/**
 * @param {object} state
 */
function optimize(state) {
  const data = { currency: state.currency, locations: Object.keys(state.locations) };
  state.sliders.forEach(nutrient => {
    if (!nutrient.active) return;
    data[`${nutrient.id}_lower`] = nutrient.lower;
    data[`${nutrient.id}_upper`] = nutrient.upper;
  });
  fetch("/optimize.csv", { body: JSON.stringify(data), method: "POST", headers: { "Content-Type": "application/json" } })
    .then(response => response.text())
    .then(text => csvParse(text, autoType))
    .then(data => {
      Result(data, state.currency);
      Sliders(data, state.sliders);
    });
}

// Global state
var state = {
  currency: "EUR",
  sliders: csvParse(document.getElementById("slider-csv-data").textContent, autoType), // Default slider data
  mapTransform: { k: 4096, x: 480, y: 250 },
  locations: {}
};
state = restoreState() || state; // Restore state from localStorage or use default
state = reactive(state); // Make state reactive
registerCheckBoxes(state);
registerCurrencySelect(state);

const locationData = await csv("/locations.csv", autoType);
Locations(locationData, state);

effect(() => persistState(state));
effect(() => optimize(state));
