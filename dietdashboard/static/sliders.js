import * as d3 from './d3.js';
import { handleOptimitzationInputs, isVisible } from './index.js';
// Inspired by https://observablehq.com/@sarah37/snapping-range-slider-with-d3-brush

// Function to initialize sliders and bars
function initializeSliders() {
    // Select all slider containers
    const containers = document.querySelectorAll('.slider-container');
    containers.forEach(container => {
        const min = Number(container.dataset.min);
        const max = Number(container.dataset.max);
        const lower = Number(container.dataset.lower);
        const upper = Number(container.dataset.upper);
        const svg = d3.select(container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', 50)
            .attr('data-nutrient', container.id); // Store nutrient name as data attribute

        // Store configuration in data attributes
        svg.attr('data-domain-min', min)
           .attr('data-domain-max', max)
           .attr('data-container-id', container.id);

        const margin = { top: 5, right: 10, bottom: 20, left: 10 };
        const width = container.clientWidth - margin.left - margin.right;
        const height = +svg.attr('height') - margin.top - margin.bottom;
        const nTicks = 10; // Adjust number of ticks as needed

        svg.attr('data-range-width', width);

        const x = d3.scaleLinear()
            .domain([min, max])
            .range([0, width]);

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // Position the axis at the bottom
        const axisYPosition = height;
        const xAxis = d3.axisBottom(x)
            .ticks(nTicks)
            .tickSize(6) // Ticks pointing down
            .tickPadding(3);

        g.append('g')
            .attr('class', 'x axis')
            .attr('transform', `translate(0,${axisYPosition})`)
            .call(xAxis)
            .selectAll('text')
            .style('text-anchor', 'middle');

        // Initialize empty stacked bar over the x-axis
        const barHeight = 10;
        const barYPosition = axisYPosition - barHeight - 2; // Position above the axis

        // Store bar configuration in data attributes
        svg.attr('data-bar-height', barHeight)
           .attr('data-bar-y-position', barYPosition);

        const barGroup = g.append('g')
            .attr('class', 'stacked-bar');

        // Define brush extent over the axis line with thinner height
        const brushHeight = 4; // Set brush height to a thin value (e.g., 4 pixels)
        const brushYPosition = axisYPosition - brushHeight / 2;
        const brushSelection = d3.brushX()
            .extent([[0, brushYPosition], [width, brushYPosition + brushHeight]])
            .on('brush', brushed)
            .on('end', brushended);

        // Add brush group AFTER the stacked bar so it appears on top
        const brushGroup = g.append('g')
            .attr('class', 'brush')
            .call(brushSelection);

        const handle = brushGroup.selectAll('.handle--custom')
            .data([{ type: 'w' }, { type: 'e' }])
            .enter().append('g')
            .attr('class', 'handle--custom')
            .attr('cursor', 'ew-resize');

        handle.append('circle')
            .attr('r', 7)
            .attr('cy', axisYPosition);

        // Set initial brush position
        brushGroup.call(brushSelection.move, [x(lower), x(upper)]);

        function brushed(event) {
            if (event.selection) {
                // Update custom handle positions
                handle.attr("transform", (d, i) => {
                    return "translate(" + [event.selection[i], 0] + ")";
                });
            }
        }

        function brushended(event) {
            if (!event.sourceEvent) return; // Only transition after input
            const [lower, upper] = event.selection.map(x.invert).map(Math.round);
            d3.select(this).transition().call(brushSelection.move, [lower, upper].map(x));
            container.dataset.lower = lower;
            container.dataset.upper = upper;
            handleOptimitzationInputs(); // Ensure this function is defined elsewhere
        }
    });
}

export function updateBars(products) {
    // Select all slider containers
    const containers = document.querySelectorAll('.slider-container');

    containers.forEach(container => {
        // Skip hidden containers
        if (!isVisible(container)) return;
        const min = Number(container.dataset.min);
        const max = Number(container.dataset.max);

        const nutrientName = container.id;
        const svgElement = container.querySelector('svg');
        if (!svgElement) return; // Skip if SVG doesn't exist

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

        // Get the segments data for this nutrient
        const segments = products.map((product, i) => {
            return {
                i: i,
                id: product.id,
                name: product.product_name,
                level: Number(product[nutrientName]),
            };
        });

        // Calculate cumulative values using actual levels
        let cum = 0;
        segments.forEach((d) => {
            d.startValue = cum;
            cum += d.level;
            d.endValue = cum;
        });

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
            .attr('width', 0) // Start with zero width for transition
        segmentGroupsEnter.append('text')
            .attr('class', 'segment-label')
            .attr('y', barYPosition - 5)
            .text(d => d.name)
            .attr('opacity', 0);

        // Merge entering and updating segments
        const segmentGroupsMerge = segmentGroupsEnter.merge(segmentGroups);

        // Update positions and sizes of rectangles for both entering and updating segments
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
            .attr('x', d => x((d.startValue + d.endValue) / 2))  // Text placement
            .text(d => d.name);

        // Ensure event listeners are attached to updated segments
        segmentGroupsMerge.select('.segment')
            .on('mouseover', function (event, d) {
                d3.select(this.parentNode).select('.segment-label')
                    .attr('opacity', 1);
            })
            .on('mouseout', function (event, d) {
                d3.select(this.parentNode).select('.segment-label')
                    .attr('opacity', 0);
            });
    });
}

// Call the initialize function once after DOM content is loaded
document.addEventListener('DOMContentLoaded', initializeSliders);
