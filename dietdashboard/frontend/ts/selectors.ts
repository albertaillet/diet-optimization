import { handleOptimizationInputs } from "./index";

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

export function initNutrientSelectors(): void {
  // Set up nutrient checkbox listeners
  document.querySelectorAll<HTMLInputElement>(".nutrient-checkbox").forEach(checkbox => {
    checkbox.addEventListener("change", () => handleCheckboxChange(checkbox));
    toggleSliderRowVisibility(checkbox.value, checkbox.checked);
  });
  // Set up select all/deselect all buttons
  setupAllButton(".select-all-btn", true); // Set up select all button
  setupAllButton(".deselect-all-btn", false); // Set up deselect all button
}
