import { Locations } from "./components/locations";
import { Result } from "./components/result";

import { Objective } from "./components/objective";
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
 * @param {State} state
 */
function optimize(state) {
  const result = select("#result");
  const data = { objective: state.objective, locations: Object.keys(state.locations) };
  state.sliders.forEach(nutrient => {
    if (!nutrient.active) return;
    data[`${nutrient.id}_lower`] = nutrient.lower;
    data[`${nutrient.id}_upper`] = nutrient.upper;
  });
  fetch("/optimize.csv", { body: JSON.stringify(data), method: "POST", headers: { "Content-Type": "application/json" } })
    .then(response => Promise.all([response.headers.get("Content-Type"), response.text()]))
    .then(([contentType, text]) => {
      if (!contentType.includes("text/csv")) {
        state.resultData = [];
        result.html(text);
      } else {
        state.resultData = csvParse(text, autoType);
        Result(result, state.resultData);
      }
      if (state.inputTabs.current === "sliders-tab") {
        SlidersTableBody(select("#slider-table-body"), state.resultData, state.sliders);
      }
    });
}

/** Global state object
 * @type {State}
 */
var state = {
  sliders: csvParse(document.getElementById("slider-csv-data").textContent, autoType), // Default slider data
  mapTransform: { k: 4062, x: 415, y: 875 },
  locations: defaultLocations,
  objective: "price", // Default objective function
  resultData: [],
  inputTabs: { current: "sliders-tab" },
  brushMode: null
};
state = { ...state, ...restoreState() };

const locationData = await csv("/locations.csv", autoType);

const tabs = [
  { id: "sliders-tab", name: "Nutrient Targets", component: parent => Sliders(parent, state.resultData, state.sliders) },
  { id: "locations-tab", name: "Location Selection", component: parent => Locations(parent, locationData, state) },
  { id: "objective-tab", name: "Objective Function", component: parent => Objective(parent, state) }
];

/**
 * @param {State} state
 */
function App(state) {
  Tabs(select("#input-tabs"), tabs, state.inputTabs);
}
// Redraw on resize
window.addEventListener("resize", () => {
  if (state.inputTabs.current === "sliders-tab") {
    SlidersTableBody(select("#slider-table-body"), state.resultData, state.sliders);
  }
});

App(state);
handleStateChange();
