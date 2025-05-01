import { handleStateChange } from "../index";

/**
 * @param {object} state
 * @param {HTMLElement} button
 * @param {boolean} checked
 */
function handleAllButton(state, button, checked) {
  button.addEventListener("click", event => {
    document.querySelectorAll(`.nutrient-checkbox[data-category="${event.target.dataset.category}"]`).forEach(checkbox => {
      checkbox.checked = checked;
      state.sliders.find(n => n.id === checkbox.value).active = checked;
    });
    handleStateChange();
  });
}

/**
 * @param {object} state
 */
export function registerCheckBoxes(state) {
  // Set up nutrient checkbox listeners
  document.querySelectorAll(".nutrient-checkbox").forEach(checkbox =>
    checkbox.addEventListener("change", () => {
      state.sliders.find(n => n.id === checkbox.value).active = checkbox.checked;
      handleStateChange();
    })
  );
  document.querySelectorAll(".select-all-btn").forEach(btn => handleAllButton(state, btn, true)); // Set up select all button
  document.querySelectorAll(".deselect-all-btn").forEach(btn => handleAllButton(state, btn, false)); // Set up deselect all button
  state.sliders.forEach(nutrient => {
    const checkbox = document.querySelector(`.nutrient-checkbox[value="${nutrient.id}"]`);
    checkbox ? (checkbox.checked = nutrient.active) : null;
  });
}
