import { csvParse } from "./d3";
import { initMap } from "./map";
import { updateResult } from "./result";
import { initSliders } from "./sliders";

const optimizationInputs = () => document.querySelectorAll("[data-optimization]");
export function isVisible(element) {
  return element.offsetParent !== null;
}

export function handleOptimitzationInputs() {
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
      updateResult(csv);
      if (false) {
        initSliders(csv);
      }
    });
}

function toggleSliderRowVisibility(sliderRowId, isChecked) {
  return; // Todo: fix
  document.getElementById(`slider-row-${sliderRowId}`).style.display = isChecked ? "" : "none";
}

function handleCheckboxChange(checkbox) {
  toggleSliderRowVisibility(checkbox.value, checkbox.checked);
  handleOptimitzationInputs();
}

// Function that sets up the event listeners for the select all and deselect all buttons
// It takes a selector for the buttons and a boolean indicating whether to check or uncheck the boxes
function handleAllButton(selector, checked) {
  function handleAllButton(e, c) {
    e.preventDefault();
    const category = e.target.dataset.category;
    const checkboxes = document.querySelectorAll(`.nutrient-checkbox[data-category="${category}"]`);
    checkboxes.forEach(checkbox => {
      checkbox.checked = c;
      toggleSliderRowVisibility(checkbox.value, c);
    });
    handleOptimitzationInputs();
  }
  document.querySelectorAll(selector).forEach(btn => btn.addEventListener("click", e => handleAllButton(e, checked)));
}
document.addEventListener("DOMContentLoaded", () => {
  optimizationInputs().forEach(element => {
    element.addEventListener("change", handleOptimitzationInputs); // Set up optimization input change listeners
  });

  // Set up nutrient checkbox listeners
  document.querySelectorAll(".nutrient-checkbox").forEach(checkbox => {
    checkbox.addEventListener("change", () => handleCheckboxChange(checkbox));
    toggleSliderRowVisibility(checkbox.value, checkbox.checked);
  });

  handleAllButton(".select-all-btn", true); // Set up select all button
  handleAllButton(".deselect-all-btn", false); // Set up deselect all button
  initMap(); // Initialize the map
  handleOptimitzationInputs(); // Initialize optimization
});
