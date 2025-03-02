import { updateBars } from './sliders.js';

function optimizationInput() { return document.querySelectorAll('[data-optimization]'); }

export function handleOptimitzationInputs() {
    const data = {};
    optimizationInput().forEach(function (element) {
        // TODO: Fix this, the checkbox unchecking is not working
        if ((element.type === 'checkbox' || element.type === 'radio')) {
            if (element.checked) {
                if (!data[element.dataset.optimization]) { data[element.dataset.optimization] = []; }
                data[element.dataset.optimization].push(element.value);  // Nutrients
            }
        } else if (element.tagName.toLowerCase() === 'select') {
            data[element.dataset.optimization] = element.value;  // Currency
        } else if (element.tagName.toLowerCase() === 'input') {
            if (!data[element.dataset.optimization]) { data[element.dataset.optimization] = []; }
            data[element.dataset.optimization].push(element.value);  // Slider selections
        }
    });
    fetch('/optimize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.text())
        .then(result => { document.getElementById('result').innerHTML = result })
        .catch(error => console.error('Error:', error))
        .then(updateBars)
}
function toggleSliderRowVisibility(sliderRow, isChecked) {
    // Toggle visibility of the slider row based on the checkbox state
    if (sliderRow) { sliderRow.style.display = isChecked ? '' : 'none' }
}
document.addEventListener('DOMContentLoaded', () => {
    optimizationInput().forEach((element) => {
        element.addEventListener('change', handleOptimitzationInputs);
    });
    handleOptimitzationInputs();

    document.querySelectorAll('.nutrient-checkbox').forEach(checkbox => {
        const sliderRow = document.getElementById(`slider-row-${checkbox.value}`);

        // Add event listener to the checkbox
        checkbox.addEventListener('change', () => {
            toggleSliderRowVisibility(sliderRow, checkbox.checked);
        });

        // Initialize visibility based on initial checkbox state
        toggleSliderRowVisibility(sliderRow, checkbox.checked);
    });
});
