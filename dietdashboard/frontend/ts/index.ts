import { csvParse } from "./d3";
import { initMap } from "./map";
import { updateResultTable } from "./result";
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

function toggleSliderRowVisibility(sliderRowId: string, isChecked: boolean): void {
  document.getElementById(`slider-row-${sliderRowId}`).style.display = isChecked ? "" : "none";
}

function handleCheckboxChange(checkbox: HTMLInputElement): void {
  toggleSliderRowVisibility(checkbox.value, checkbox.checked);
  handleOptimizationInputs();
}

/**
 * Sets up the event listeners for the select-all or deselect-all buttons.
 * @param selector The CSS selector for the buttons.
 * @param checked Whether to check or uncheck the boxes in that category.
 */
function setupAllButton(selector: string, checked: boolean): void {
  function handleAllButtonClick(e: Event, c: boolean): void {
    e.preventDefault();
    const category = e.target.dataset.category;
    const checkboxes = document.querySelectorAll<HTMLInputElement>(`.nutrient-checkbox[data-category="${category}"]`);
    checkboxes.forEach(checkbox => {
      checkbox.checked = c;
      toggleSliderRowVisibility(checkbox.value, c);
    });
    handleOptimizationInputs();
  }
  document.querySelectorAll(selector).forEach(btn => btn.addEventListener("click", e => handleAllButtonClick(e, checked)));
}
document.addEventListener("DOMContentLoaded", () => {
  optimizationInputs().forEach(element => {
    element.addEventListener("change", handleOptimizationInputs);
  });

  // Set up nutrient checkbox listeners
  document.querySelectorAll<HTMLInputElement>(".nutrient-checkbox").forEach(checkbox => {
    checkbox.addEventListener("change", () => handleCheckboxChange(checkbox));
    toggleSliderRowVisibility(checkbox.value, checkbox.checked);
  });

  setupAllButton(".select-all-btn", true); // Set up select all button
  setupAllButton(".deselect-all-btn", false); // Set up deselect all button
  initMap(); // Initialize the map
  handleOptimizationInputs(); // Initialize optimization
});
