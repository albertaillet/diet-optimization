import { csvParse } from './d3';
import { updateResultTable } from './result';
import { updateBars } from './sliders';

function optimizationInput() { return document.querySelectorAll('[data-optimization]'); };

export function isVisible(element) {return element.offsetParent !== null}

export function handleOptimitzationInputs() {
    const data = {};
    optimizationInput().forEach(element => {
        if (element.tagName.toLowerCase() === 'select') {
            data[element.dataset.optimization] = element.value;  // Currency
        } else if (element.dataset.optimization == 'slider') {
            if (isVisible(element))
            {data[element.id] = [Number(element.dataset.lower), Number(element.dataset.upper)]}
            else {}
        } else {
            console.log("Error")
        }
    });
    fetch('/optimize.csv', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.text())
        .then(text => csvParse(text))
        .then(csv => {updateResultTable(csv); updateBars(csv);})
}
function toggleSliderRowVisibility(sliderRow, isChecked) {
    // Toggle visibility of the slider row based on the checkbox state
    sliderRow.style.display = isChecked ? '' : 'none'
}
document.addEventListener('DOMContentLoaded', () => {
    optimizationInput().forEach((element) => {
        element.addEventListener('change', handleOptimitzationInputs);
    });
    handleOptimitzationInputs();

    // Handle individual nutrient checkboxes
    document.querySelectorAll('.nutrient-checkbox').forEach(checkbox => {
        const sliderRow = document.getElementById(`slider-row-${checkbox.value}`);

        // Add event listener to the checkbox
        checkbox.addEventListener('change', () => {
            toggleSliderRowVisibility(sliderRow, checkbox.checked);
            handleOptimitzationInputs();
        });

        // Initialize visibility based on initial checkbox state
        toggleSliderRowVisibility(sliderRow, checkbox.checked);
    });

    // Handle "Select All" buttons
    document.querySelectorAll('.select-all-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const category = button.dataset.category;
            document.querySelectorAll(`.nutrient-checkbox[data-category="${category}"]`).forEach(checkbox => {
                checkbox.checked = true;
                const sliderRow = document.getElementById(`slider-row-${checkbox.value}`);
                toggleSliderRowVisibility(sliderRow, true);
            });
            handleOptimitzationInputs();
        });
    });

    // Handle "Deselect All" buttons
    document.querySelectorAll('.deselect-all-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const category = button.dataset.category;
            document.querySelectorAll(`.nutrient-checkbox[data-category="${category}"]`).forEach(checkbox => {
                checkbox.checked = false;
                const sliderRow = document.getElementById(`slider-row-${checkbox.value}`);
                toggleSliderRowVisibility(sliderRow, false);
            });
            handleOptimitzationInputs();
        });
    });
});
