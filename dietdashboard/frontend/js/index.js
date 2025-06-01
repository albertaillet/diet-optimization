import { registerCurrencySelect } from "./components/currency";
import { Locations } from "./components/locations";
import { Result } from "./components/result";

import { Sliders, SlidersTableBody } from "./components/sliders";
import { Tabs } from "./components/tabs";
import { autoType, csv, csvParse, select } from "./d3";
import { defaultLocations } from "./defaultLocations";

export function handleStateChange() {
  persistState();
  optimize(state);
}

export const persistState = () => localStorage.setItem("state", JSON.stringify(state));
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
      state.resultData = data;
      Result(select("#result"), state);
      if (state.inputTabs.current === "sliders-tab") {
        SlidersTableBody(select("#slider-table-body"), state.resultData, state.sliders);
      }
    });
}

// Global state
var state = {
  currency: "EUR",
  sliders: csvParse(document.getElementById("slider-csv-data").textContent, autoType), // Default slider data
  mapTransform: { k: 4062, x: 415, y: 875 },
  locations: defaultLocations,
  resultData: [],
  inputTabs: { current: "sliders-tab" },
  brushMode: null
};
state = { ...state, ...restoreState() };
registerCurrencySelect(state);

const locationData = await csv("/locations.csv", autoType);

const tabs = [
  { id: "sliders-tab", name: "Nutrient Targets", component: parent => Sliders(parent, state.resultData, state.sliders) },
  { id: "locations-tab", name: "Location Selection", component: parent => Locations(parent, locationData, state) }
];

function App(state) {
  Tabs(select("#input-tabs"), tabs, state.inputTabs);
  Result(select("#result"), state);
}

App(state);
handleStateChange();
