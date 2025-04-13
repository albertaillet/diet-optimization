import { csvParse } from "./d3";
import { updateResultTable } from "./result";
import { updateBars } from "./sliders";

function optimizationInput() {
  return document.querySelectorAll("[data-optimization]");
}

export function isVisible(element) {
  return element.offsetParent !== null;
}

export function handleOptimitzationInputs() {
  const data = {};
  optimizationInput().forEach(element => {
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
    });
}

function toggleSliderRowVisibility(sliderRowId, isChecked) {
  document.getElementById(`slider-row-${sliderRowId}`).style.display = isChecked ? "" : "none";
}

function handleCheckboxChange(checkbox) {
  toggleSliderRowVisibility(checkbox.value, checkbox.checked);
  handleOptimitzationInputs();
}

function handleAllButton(e, select) {
  e.preventDefault();
  const category = e.target.dataset.category;
  const checkboxes = document.querySelectorAll(`.nutrient-checkbox[data-category="${category}"]`);
  checkboxes.forEach(checkbox => {
    checkbox.checked = select;
    toggleSliderRowVisibility(checkbox.value, select);
  });
  handleOptimitzationInputs();
}
document.addEventListener("DOMContentLoaded", () => {
  optimizationInput().forEach(element => {
    element.addEventListener("change", handleOptimitzationInputs); // Set up optimization input change listeners
  });
  handleOptimitzationInputs(); // Initialize optimization

  // Set up nutrient checkbox listeners
  document.querySelectorAll(".nutrient-checkbox").forEach(checkbox => {
    checkbox.addEventListener("change", () => handleCheckboxChange(checkbox));
    toggleSliderRowVisibility(checkbox.value, checkbox.checked);
  });

  // Set up Select All buttons
  document.querySelectorAll(".select-all-btn").forEach(button => {
    button.addEventListener("click", e => handleAllButton(e, true));
  });

  // Set up Deselect All buttons
  document.querySelectorAll(".deselect-all-btn").forEach(button => {
    button.addEventListener("click", e => handleAllButton(e, false));
  });
});
