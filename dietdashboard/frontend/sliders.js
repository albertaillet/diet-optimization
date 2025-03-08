import * as d3 from './d3';
import { handleOptimitzationInputs, isVisible } from './index';
// Inspired by https://observablehq.com/@sarah37/snapping-range-slider-with-d3-brush

// Common configuration values
const CONFIG = {
    margin: { top: 5, right: 10, bottom: 20, left: 10 },
    svgHeight: 50,
    nTicks: 10,
    barHeight: 10,
    brushHeight: 4,
    handleRadius: 7
};

/**
 * Creates an SVG element for a slider with D3
 * @param {HTMLElement} container - The container element
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @param {number} lower - Lower bound
 * @param {number} upper - Upper bound
 * @returns {Object} Object containing the SVG and scale
 */
function createSliderSVG(container, min, max, lower, upper) {
    // Create SVG element
    const svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', CONFIG.svgHeight)
        .attr('data-nutrient', container.id);

    // Store configuration in data attributes
    svg.attr('data-domain-min', min)
       .attr('data-domain-max', max)
       .attr('data-container-id', container.id);

    const width = container.clientWidth - CONFIG.margin.left - CONFIG.margin.right;
    const height = CONFIG.svgHeight - CONFIG.margin.top - CONFIG.margin.bottom;

    svg.attr('data-range-width', width);

    // Create scale
    const x = d3.scaleLinear()
        .domain([min, max])
        .range([0, width]);

    return { svg, x, width, height };
}

/**
 * Adds axis to the slider
 * @param {d3.Selection} svg - The D3 selection of the SVG element
 * @param {d3.Scale} x - The D3 scale
 * @param {number} height - The height of the SVG
 * @returns {Object} Object containing the group element and y positions
 */
function createSliderAxis(svg, x, height) {
    const g = svg.append('g')
        .attr('transform', `translate(${CONFIG.margin.left},${CONFIG.margin.top})`);

    const axisYPosition = height;

    // Create X-axis
    const xAxis = d3.axisBottom(x)
        .ticks(CONFIG.nTicks)
        .tickSize(6)
        .tickPadding(3);

    g.append('g')
        .attr('class', 'x axis')
        .attr('transform', `translate(0,${axisYPosition})`)
        .call(xAxis)
        .selectAll('text')
        .style('text-anchor', 'middle');

    // Calculate bar position
    const barYPosition = axisYPosition - CONFIG.barHeight - 2;

    // Store bar configuration
    svg.attr('data-bar-height', CONFIG.barHeight)
       .attr('data-bar-y-position', barYPosition);

    // Create bar group
    const barGroup = g.append('g')
        .attr('class', 'stacked-bar');

    return { g, axisYPosition, barYPosition, barGroup };
}

/**
 * Adds brush interaction to the slider
 * @param {d3.Selection} g - The D3 group element
 * @param {d3.Scale} x - The D3 scale
 * @param {number} axisYPosition - The Y position of the axis
 * @param {number} width - The width of the SVG
 * @param {HTMLElement} container - The container element
 * @param {number} lower - Lower bound
 * @param {number} upper - Upper bound
 */
function createSliderBrush(g, x, axisYPosition, width, container, lower, upper) {
    const brushYPosition = axisYPosition - CONFIG.brushHeight / 2;

    const brushSelection = d3.brushX()
        .extent([[0, brushYPosition], [width, brushYPosition + CONFIG.brushHeight]])
        .on('brush', brushed)
        .on('end', brushended);

    // Add brush group
    const brushGroup = g.append('g')
        .attr('class', 'brush')
        .call(brushSelection);

    // Add custom handles
    const handle = brushGroup.selectAll('.handle--custom')
        .data([{ type: 'w' }, { type: 'e' }])
        .enter().append('g')
        .attr('class', 'handle--custom')
        .attr('cursor', 'ew-resize');

    handle.append('circle')
        .attr('r', CONFIG.handleRadius)
        .attr('cy', axisYPosition);

    // Set initial brush position
    brushGroup.call(brushSelection.move, [x(lower), x(upper)]);

    // Brush event handlers
    function brushed(event) {
        if (event.selection) {
            handle.attr("transform", (d, i) => {
                return "translate(" + [event.selection[i], 0] + ")";
            });
        }
    }

    function brushended(event) {
        if (!event.sourceEvent) return;
        const [lower, upper] = event.selection.map(x.invert).map(Math.round);
        d3.select(this).transition().call(brushSelection.move, [lower, upper].map(x));
        container.dataset.lower = lower;
        container.dataset.upper = upper;
        handleOptimitzationInputs();
    }
}

/**
 * Initializes or updates a slider
 * @param {HTMLElement} container - The container element
 * @param {boolean} isUpdate - Whether this is an update or initial creation
 */
function setupSlider(container, isUpdate = false) {
    const min = Number(container.dataset.min);
    const max = Number(container.dataset.max);
    let lower = Number(container.dataset.lower);
    let upper = Number(container.dataset.upper);

    // If updating, ensure values are within range
    if (isUpdate) {
        lower = Math.max(min, Math.min(lower, max));
        upper = Math.max(min, Math.min(upper, max));
        container.dataset.lower = lower;
        container.dataset.upper = upper;

        // Remove existing SVG if updating
        const existingSvg = container.querySelector('svg');
        if (existingSvg) {
            existingSvg.remove();
        }
    }

    // Create SVG and scale
    const { svg, x, width, height } = createSliderSVG(container, min, max, lower, upper);

    // Add axis and bar group
    const { g, axisYPosition, barYPosition, barGroup } = createSliderAxis(svg, x, height);

    // Add brush interaction
    createSliderBrush(g, x, axisYPosition, width, container, lower, upper);
}

/**
 * Initialize all sliders on the page
 */
function initializeSliders() {
    const containers = document.querySelectorAll('.slider-container');
    containers.forEach(setupSlider);
}

/**
 * Update the range of a slider
 * @param {string} sliderId - ID of the slider to update
 * @param {number} newMin - New minimum value
 * @param {number} newMax - New maximum value
 */
export function updateSliderRange(sliderId, newMin, newMax) {
    const container = document.getElementById(sliderId);
    if (!container) return;

    // Update data attributes
    container.dataset.min = newMin;
    container.dataset.max = newMax;

    // Re-initialize the slider with updated values
    setupSlider(container, true);
}

/**
 * Update the bar charts in sliders with product data
 * @param {Array} products - Array of product data
 */
export function updateBars(products) {
    const containers = document.querySelectorAll('.slider-container');

    containers.forEach(container => {
        // Skip hidden containers
        if (!isVisible(container)) return;

        const min = Number(container.dataset.min);
        const max = Number(container.dataset.max);
        const nutrientName = container.id;

        const svgElement = container.querySelector('svg');
        if (!svgElement) return;

        const svg = d3.select(svgElement);

        // Recreate scale from stored values
        const rangeWidth = Number(svg.attr('data-range-width'));
        const barYPosition = Number(svg.attr('data-bar-y-position'));
        const barHeight = Number(svg.attr('data-bar-height'));

        const x = d3.scaleLinear()
            .domain([min, max])
            .range([0, rangeWidth]);

        // Get the barGroup within this SVG
        const barGroup = svg.select('.stacked-bar');

        // Create segments data from products
        const segments = createSegmentsData(products, nutrientName);

        // Update the visualization with segments
        updateSegments(barGroup, segments, x, barYPosition, barHeight);
    });
}

/**
 * Create segment data from products for a specific nutrient
 * @param {Array} products - Array of product data
 * @param {string} nutrientName - Name of the nutrient
 * @returns {Array} Array of segment data
 */
function createSegmentsData(products, nutrientName) {
    // Map products to segments
    const segments = products.map((product, i) => ({
        i: i,
        id: product.id,
        name: product.product_name,
        level: Number(product[nutrientName]),
    }));

    // Calculate cumulative values
    let cum = 0;
    segments.forEach((d) => {
        d.startValue = cum;
        cum += d.level;
        d.endValue = cum;
    });

    return segments;
}

/**
 * Update the segments visualization with new data
 * @param {d3.Selection} barGroup - The D3 selection of the bar group
 * @param {Array} segments - Array of segment data
 * @param {d3.Scale} x - The D3 scale
 * @param {number} barYPosition - The Y position of the bars
 * @param {number} barHeight - The height of the bars
 */
function updateSegments(barGroup, segments, x, barYPosition, barHeight) {
    // Data join without key function (match by index)
    const segmentGroups = barGroup.selectAll('.segment-group')
        .data(segments);

    // EXIT selection: Remove old elements
    segmentGroups.exit()
        .transition()
        .duration(100)
        .style('opacity', 0)
        .remove();

    // ENTER selection: Create new elements
    const segmentGroupsEnter = segmentGroups.enter()
        .append('g')
        .attr('class', 'segment-group');

    // Append rectangles to entering segments
    segmentGroupsEnter.append('rect')
        .attr('class', 'segment')
        .attr('y', barYPosition)
        .attr('height', barHeight)
        .attr('width', 0); // Start with zero width for transition

    segmentGroupsEnter.append('text')
        .attr('class', 'segment-label')
        .attr('y', barYPosition - 5)
        .text(d => d.name)
        .attr('opacity', 0);

    // Merge entering and updating segments
    const segmentGroupsMerge = segmentGroupsEnter.merge(segmentGroups);

    // Update positions and sizes of rectangles
    segmentGroupsMerge.select('.segment')
        .transition()
        .duration(750)
        .attr('x', d => x(d.startValue))
        .attr('width', d => x(d.endValue) - x(d.startValue))
        .attr('fill', (d, i) => d3.schemeTableau10[d.i % 10]);

    // Update positions and text of labels
    segmentGroupsMerge.select('.segment-label')
        .transition()
        .duration(750)
        .attr('x', d => x((d.startValue + d.endValue) / 2))
        .text(d => d.name);

    // Add hover interactions
    segmentGroupsMerge.select('.segment')
        .on('mouseover', function (event, d) {
            d3.select(this.parentNode).select('.segment-label')
                .attr('opacity', 1);
        })
        .on('mouseout', function (event, d) {
            d3.select(this.parentNode).select('.segment-label')
                .attr('opacity', 0);
        });
}

/**
 * Setup modal dialog for editing slider ranges
 */
function setupRangeEditModal() {
    const modal = document.getElementById('rangeModal');
    const closeBtn = document.querySelector('.close-modal');
    const cancelBtn = document.getElementById('cancelBtn');
    const form = document.getElementById('rangeForm');
    const minInput = document.getElementById('minValue');
    const maxInput = document.getElementById('maxValue');
    const currentSliderId = document.getElementById('currentSliderId');
    const modalTitle = document.getElementById('modalTitle');

    // Setup modal close actions
    setupModalCloseActions(modal, closeBtn, cancelBtn);

    // Handle form submission
    setupModalFormSubmission(form, currentSliderId, minInput, maxInput, modal);

    // Setup edit buttons
    setupEditButtons(modalTitle, currentSliderId, minInput, maxInput, modal);
}

/**
 * Setup modal close actions
 * @param {HTMLElement} modal - The modal element
 * @param {HTMLElement} closeBtn - The close button
 * @param {HTMLElement} cancelBtn - The cancel button
 */
function setupModalCloseActions(modal, closeBtn, cancelBtn) {
    // Close modal when clicking the X button or cancel button
    [closeBtn, cancelBtn].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
    });

    // Close modal when clicking outside the modal content
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

/**
 * Setup modal form submission
 * @param {HTMLElement} form - The form element
 * @param {HTMLElement} currentSliderId - The input for current slider ID
 * @param {HTMLElement} minInput - The input for minimum value
 * @param {HTMLElement} maxInput - The input for maximum value
 * @param {HTMLElement} modal - The modal element
 */
function setupModalFormSubmission(form, currentSliderId, minInput, maxInput, modal) {
    if (form) {
        form.addEventListener('submit', (event) => {
            event.preventDefault();

            const sliderId = currentSliderId.value;
            const newMin = parseInt(minInput.value, 10);
            const newMax = parseInt(maxInput.value, 10);

            // Validate input
            if (newMin >= newMax) {
                alert('Minimum value must be less than maximum value');
                return;
            }

            // Update the slider
            updateSliderRange(sliderId, newMin, newMax);

            // Close the modal
            modal.style.display = 'none';
        });
    }
}

/**
 * Setup edit buttons
 * @param {HTMLElement} modalTitle - The modal title element
 * @param {HTMLElement} currentSliderId - The input for current slider ID
 * @param {HTMLElement} minInput - The input for minimum value
 * @param {HTMLElement} maxInput - The input for maximum value
 * @param {HTMLElement} modal - The modal element
 */
function setupEditButtons(modalTitle, currentSliderId, minInput, maxInput, modal) {
    // Set up click handlers for all "Edit Range" buttons
    document.querySelectorAll('.range-edit-btn').forEach(button => {
        button.addEventListener('click', () => {
            const sliderId = button.dataset.sliderId;
            const sliderName = button.dataset.sliderName;
            const sliderUnit = button.dataset.sliderUnit;
            const sliderContainer = document.getElementById(sliderId);

            if (sliderContainer) {
                // Set modal title
                modalTitle.textContent = `Edit Range: ${sliderName} (${sliderUnit})`;

                // Set current slider ID
                currentSliderId.value = sliderId;

                // Set current min/max values
                minInput.value = sliderContainer.dataset.min;
                maxInput.value = sliderContainer.dataset.max;

                // Show the modal
                modal.style.display = 'block';
            }
        });
    });
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeSliders();
    setupRangeEditModal();
});
