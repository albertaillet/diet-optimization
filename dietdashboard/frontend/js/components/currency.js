import { handleStateChange } from "../index.js";

const currencySelect = document.getElementById("currency-select");

/**
 * @param {object} state
 */
export function registerCurrencySelect(state) {
  currencySelect.value = state.currency;
  currencySelect.addEventListener("change", event => {
    state.currency = event.target.value;
    handleStateChange();
  });
}
