import { csvParse } from "./d3";
import { initMap } from "./map";
import { updateResultTable } from "./result";
import { initNutrientSelectors } from "./selectors";
import { updateBars } from "./sliders";

const optimizationInputs = () => document.querySelectorAll("[data-optimization]");
export const isVisible = element => element.offsetParent !== null;

export function handleOptimizationInputs(): void {
  const data = {};
  optimizationInputs().forEach(element => {
    if (element.tagName.toLowerCase() === "select") {
      data[element.dataset.optimization] = element.value;
    } else if (element.dataset.optimization === "slider" && isVisible(element)) {
      data[element.id] = [Number(element.dataset.lower), Number(element.dataset.upper)];
    }
  });
  fetch("/optimize.csv", { body: JSON.stringify(data), method: "POST", headers: { "Content-Type": "application/json" } })
    .then(response => response.text())
    .then(text => csvParse(text))
    .then(csv => {
      updateResultTable(csv);
      updateBars(csv);
    })
    .catch(error => console.error("Error fetching and parsing optimize.csv:", error));
}

document.addEventListener("DOMContentLoaded", () => {
  optimizationInputs().forEach(element => {
    element.addEventListener("change", handleOptimizationInputs);
  });

  initMap(); // Initialize the map
  initNutrientSelectors(); // Initialize nutrient selector
  handleOptimizationInputs(); // Initialize optimization
});
