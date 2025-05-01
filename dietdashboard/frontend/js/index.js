import { Map } from "./components/map";
import { Result } from "./components/result";
import { Sliders } from "./components/sliders";
import { autoType, csv, csvParse, select } from "./d3";

export function handleStateChange() {
  persistState(state);
  optimize(state);
}

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

/**
 * @param {HTMLElement} button
 * @param {boolean} checked
 */
function handleAllButton(button, checked) {
  button.addEventListener("click", event => {
    document.querySelectorAll(`.nutrient-checkbox[data-category="${event.target.dataset.category}"]`).forEach(checkbox => {
      checkbox.checked = checked;
      state.sliders.find(n => n.id === checkbox.value).active = checked;
    });
    handleStateChange();
  });
}

// Set up nutrient checkbox listeners
document.querySelectorAll(".nutrient-checkbox").forEach(checkbox =>
  checkbox.addEventListener("change", () => {
    state.sliders.find(n => n.id === checkbox.value).active = checkbox.checked;
    handleStateChange();
  })
);
document.querySelectorAll(".select-all-btn").forEach(btn => handleAllButton(btn, true)); // Set up select all button
document.querySelectorAll(".deselect-all-btn").forEach(btn => handleAllButton(btn, false)); // Set up deselect all button

const currencySelect = document.getElementById("currency-select");
const sliderCsvData = document.getElementById("slider-csv-data");
if (!currencySelect || !sliderCsvData) {
  alert("Missing required elements in the HTML");
}

// Set up currency select listener
currencySelect.addEventListener("change", event => {
  state.currency = event.target.value;
  handleStateChange();
});

// Global state
var state = {
  currency: currencySelect.value,
  sliders: csvParse(sliderCsvData.textContent, autoType), // Default slider data
  mapTransform: { k: 4096, x: 480, y: 250 },
  locations: {}
};
state = restoreState() || state; // Restore state from localStorage or use default
console.log(state);
state.sliders.forEach(nutrient => {
  const checkbox = document.querySelector(`.nutrient-checkbox[value="${nutrient.id}"]`);
  if (checkbox) {
    checkbox.checked = nutrient.active;
  }
});

const locationData = await csv("/locations.csv", autoType);
Map(select("#map"), locationData, state); // Initialize the map
handleStateChange();
