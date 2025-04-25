import * as d3 from "./d3";
import { optimize } from "./index";
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
 * @param {object} d
 * @param {d3.Scale} x
 * @param {number} height
 * @param {number} width
 */
function setupBrush(g, d, x, height, width) {
  const { min, max, lower, upper, id } = d; // Get state from the passed object
  const brushSelection = d3
    .brushX()
    .extent([
      [0, height - CONFIG.brushHeight / 2],
      [width, height + CONFIG.brushHeight / 2]
    ])
    .on("brush", function (event) {
      if (!event.selection) return;
      handle.attr("transform", (d, i) => `translate(${event.selection[i]},0)`);
    })
    .on("end", function (event) {
      if (!event.sourceEvent) return;
      [d.lower, d.upper] = event.selection.map(x.invert);
      optimize();
    });

  const brushGroup = g.append("g").attr("class", "brush").call(brushSelection);

  const handle = brushGroup
    .selectAll(".handle--custom")
    .data([{ type: "w" }, { type: "e" }])
    .enter()
    .append("g")
    .attr("class", "handle--custom")
    .attr("cursor", "ew-resize");

  handle.append("circle").attr("r", CONFIG.handleRadius).attr("cy", height);

  // Set initial brush position
  brushGroup.call(brushSelection.move, [lower, upper].map(x));
}

/**
 * @param {Event} event
 * @param {object} d
 */
function openModal(event, d) {
  form.addEventListener("submit", event => {
    if (event.submitter.name != "save") return;
    const formData = new FormData(form);
    const newMin = Number(formData.get("minVal"));
    const newMax = Number(formData.get("maxVal"));
    // Validate input
    if (newMin >= newMax) {
      alert("Minimum value must be less than maximum value");
      return;
    }
    // Directly MUTATE the object's properties
    d.min = newMin;
    d.max = newMax;
    // Clamp existing lower/upper bounds to the new min/max range
    d.lower = Math.max(newMin, Math.min(d.lower, newMax));
    d.upper = Math.max(newMin, Math.min(d.upper, newMax));
    optimize();
  });
  modalTitle.textContent = `Edit Range: ${d.name} (${d.unit})`;
  form.elements.minVal.value = d.min;
  form.elements.maxVal.value = d.max;
  modal.showModal();
}

function displaySliderTable(selection, data) {
  selection
    .selectAll("tr")
    .data(data, d => d.id)
    .join(
      enter =>
        enter
          .append("tr")
          .call(tr =>
            tr
              .append("td")
              .style("padding", 0) // TODO: do all the styling in CSS
              .append("div")
              .attr("style", "display: flex; flex-direction: column; align-items: center;")
              .call(div =>
                div
                  .append("span")
                  .attr("style", "padding: 0.3rem; font-weight: 500; font-size: 0.85rem;")
                  .text(d => `${d.name} (${d.unit})`)
              )
              .call(div => div.append("button").text("Edit Range").on("click", openModal))
          )
          .append("td")
          .append("svg")
          .attr("width", "100%")
          .attr("height", CONFIG.svgHeight),
      update => update.select("svg"),
      exit => exit.remove()
    )
    .each(function (d) {
      const svg = d3.select(this);
      svg.selectAll("*").remove(); // Clear previous content TODO: update the content in a more efficient way
      const width = this.clientWidth - CONFIG.margin.left - CONFIG.margin.right;
      const height = CONFIG.svgHeight - CONFIG.margin.top - CONFIG.margin.bottom;
      const x = d3.scaleLinear().domain([d.min, d.max]).range([0, width]);
      const g = svg.append("g").attr("transform", `translate(${CONFIG.margin.left},${CONFIG.margin.top})`);
      g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(CONFIG.nTicks).tickSize(6).tickPadding(3));

      const bar = g.append("g").attr("class", "bar");
      setupBrush(g, d, x, height, width);
      updateSegments(bar, d.segments, x);
    });
}

/**
 * @param {Array} products
 * @param {string} nutrientId
 */
function createSegmentsData(products, nutrientId) {
  // Map products to segments
  const segments = products.map((product, i) => ({
    i: i,
    id: product.id,
    name: product.product_name,
    level: Number(product[nutrientId]) || 0
  }));

  // Calculate cumulative values
  let cum = 0;
  segments.forEach(d => {
    d.startValue = cum;
    cum += d.level;
    d.endValue = cum;
  });

  return segments;
}

/**
 * @param {d3.Selection} barGroup
 * @param {Array} segments
 * @param {d3.Scale} x
 */
function updateSegments(barGroup, segments, x) {
  // Setup bar positioning
  const height = CONFIG.svgHeight - CONFIG.margin.top - CONFIG.margin.bottom;
  const axisYPosition = height;
  const barYPosition = axisYPosition - CONFIG.barHeight - 2;
  const barHeight = CONFIG.barHeight; // From config

  // Use product ID as the key function for object constancy
  const segmentGroups = barGroup
    .selectAll("g")
    .data(segments, d => `${d.id}-${d.quantity_g}`)
    .join("g");

  // Append rectangles to entering segments (start with 0 width at final position)
  segmentGroups
    .append("rect")
    .attr("class", "segment")
    .attr("y", barYPosition)
    .attr("height", barHeight)
    .attr("x", 0)
    .attr("width", 0) // Start with zero width for transition
    .attr("fill", (d, i) => d3.schemeTableau10[d.i % 10]) // Color based on original index
    .transition()
    .duration(750)
    .attr("width", d => Math.max(0, x(d.endValue) - x(d.startValue))) // Ensure non-negative width
    .attr("x", d => x(d.startValue));

  segmentGroups
    .append("text")
    .attr("class", "segment-label")
    .attr("y", barYPosition - 5) // Position above bar
    .attr("x", d => x((d.startValue + d.endValue) / 2)) // Center based on final values
    .text(d => d.name)
    .attr("text-anchor", "middle")
    .style("font-size", "10px")
    .attr("opacity", 0); // Start hidden

  segmentGroups
    .on("pointerover", function (event, d) {
      d3.select(this).select(".segment-label").attr("opacity", 1); // TODO: do this with CSS
    })
    .on("pointerleave", function (event, d) {
      d3.select(this).select(".segment-label").attr("opacity", 0); // TODO: do this with CSS
    });
}

const modal = document.getElementById("rangeModal");
const form = document.getElementById("rangeForm");
const modalTitle = document.getElementById("modalTitle");
if (!modal || !form || !modalTitle) {
  alert("Missing modal elements");
}

// --- Main Application Logic ---
export function Sliders(productsData, sliderData) {
  sliderData.forEach(d => (d.segments = createSegmentsData(productsData, d.id)));
  const tableBody = d3.select("#slider-table-body");
  displaySliderTable(tableBody, sliderData);
}
