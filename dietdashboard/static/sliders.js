import * as d3 from './d3.js';
import { handleOptimitzationInputs } from './index.js';
// Inspired by https://observablehq.com/@sarah37/snapping-range-slider-with-d3-brush

// Object to store references to sliders and their components
const sliderComponents = {};

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
            .attr('height', 60); // Adjust height as needed

        const domainX = [min, max];
        const margin = { top: 5, right: 10, bottom: 20, left: 10 };
        const width = container.clientWidth - margin.left - margin.right;
        const height = +svg.attr('height') - margin.top - margin.bottom;
        const nTicks = 10; // Adjust number of ticks as needed

        const x = d3.scaleLinear()
            .domain(domainX)
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

        // Create custom handles
        const handle = brushGroup.selectAll('.handle--custom')
            .data([{ type: 'w' }, { type: 'e' }])
            .enter().append('g')
            .attr('class', 'handle--custom')
            .attr('cursor', 'ew-resize');

        handle.append('circle')
            .attr('r', 8)
            .attr('cy', axisYPosition); // Position handles on the axis line

        // Set initial brush position
        brushGroup.call(brushSelection.move, [x(lower), x(upper)]);

        function brushed(event) {
            if (event.selection) {
                // Update custom handle positions
                handle.attr("transform", function (d, i) {
                    return "translate(" + [event.selection[i], 0] + ")";
                });
            }
        }

        function brushended(event) {
            if (!event.sourceEvent) return; // Only transition after input
            const [lower, upper] = event.selection.map(x.invert).map(Math.round);
            d3.select(this).transition().call(brushSelection.move, [lower, upper].map(x));
            container.setAttribute('data-lower', lower)
            container.setAttribute('data-upper', upper)
            handleOptimitzationInputs(); // Ensure this function is defined elsewhere
        }

        // Store references for updating later
        sliderComponents[container.id] = {
            x: x,
            barGroup: barGroup,
            barYPosition: barYPosition,
            barHeight: barHeight,
        };
    });
}

export function updateBars(products) {
    Object.keys(sliderComponents).forEach((nutrientName) => {
        // TODO: don't run this for hidden slider rows
        const components = sliderComponents[nutrientName];
        const x = components.x;
        const barGroup = components.barGroup;
        const barYPosition = components.barYPosition;
        const barHeight = components.barHeight;

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
            .on('mouseover', function (event, d) {
                d3.select(this.parentNode).select('.segment-label')
                    .attr('opacity', 1);
            })
            .on('mouseout', function (event, d) {
                d3.select(this.parentNode).select('.segment-label')
                    .attr('opacity', 0);
            });

        // Append labels to entering segments
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
            .attr('fill', (d, i) => d3.schemeCategory10[d.i % 10]);

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
