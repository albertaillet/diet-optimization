import * as d3 from "./d3";
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
 * @param {d3.Selection} g
 * @param {d3.Scale} x
 * @param {number} axisYPosition
 * @param {number} width
 * @param {object} d
 */
function setupBrush(g, x, axisYPosition, width, d) {
  const { min, max, lower, upper, id } = d; // Get state from the passed object
  const brushYPosition = axisYPosition - CONFIG.brushHeight / 2;

  const brushSelection = d3
    .brushX()
    .extent([
      [0, brushYPosition],
      [width, brushYPosition + CONFIG.brushHeight]
    ])
    .on("brush", moveHandle)
    .on("end", brushended);

  const brushGroup = g.append("g").attr("class", "brush").call(brushSelection);

  const handle = brushGroup
    .selectAll(".handle--custom")
    .data([{ type: "w" }, { type: "e" }])
    .enter()
    .append("g")
    .attr("class", "handle--custom")
    .attr("cursor", "ew-resize");

  handle.append("circle").attr("r", CONFIG.handleRadius).attr("cy", axisYPosition);

  // Set initial brush position
  brushGroup.call(brushSelection.move, [lower, upper].map(x));

  function moveHandle(event) {
    if (!event.selection) return;
    handle.attr("transform", (d, i) => `translate(${event.selection[i]},0)`);
  }

  function brushended(event) {
    if (!event.sourceEvent) return;
    // TODO: update the lower and upper state and re-render the segments
    // const [lower, upper] = event.selection.map(x.invert);
    // d.lower = lower;
    // d.upper = upper;
  }
}

/**
 * @param {HTMLElement} container
 * @param {object} d
 * @param {Array} segments
 */
function setupSlider(d) {
  // TODO: make this reactive to the container size on resize
  const width = this.clientWidth - CONFIG.margin.left - CONFIG.margin.right;
  const height = CONFIG.svgHeight - CONFIG.margin.top - CONFIG.margin.bottom;

  const x = d3.scaleLinear().domain([d.min, d.max]).range([0, width]);
  const g = d3.select(this).append("g").attr("transform", `translate(${CONFIG.margin.left},${CONFIG.margin.top})`);
  const axisYPosition = height;
  g.append("g")
    .attr("transform", `translate(0,${axisYPosition})`)
    .call(d3.axisBottom(x).ticks(CONFIG.nTicks).tickSize(6).tickPadding(3));

  const bar = g.append("g").attr("class", "bar");
  setupBrush(g, x, axisYPosition, width, d);
  updateSegments(bar, d.segments, x);
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
    // TODO: Re-render the slider with the new min/max
  });
  modalTitle.textContent = `Edit Range: ${d.name} (${d.unit})`;
  form.elements.minVal.value = d.min;
  form.elements.maxVal.value = d.max;
  modal.showModal();
}

function displayLabelCell(selection) {
  const cell = selection
    .append("td")
    .style("padding", 0) // TODO: do all the styling in CSS
    .append("div")
    .attr("style", "display: flex; flex-direction: column; align-items: center;");
  cell
    .append("span")
    .attr("style", "padding: 0.3rem; font-weight: 500; font-size: 0.85rem;")
    .text(d => `${d.name} (${d.unit})`);
  cell.append("button").text("Edit Range").on("click", openModal);
}

function displaySliderCell(selection) {
  selection.append("td").append("svg").attr("width", "100%").attr("height", CONFIG.svgHeight).each(setupSlider);
}

function displaySliderTable(selection, sliderData) {
  selection
    .selectAll("tr")
    .data(sliderData, d => d.id) // Use unique ID as key from the source of truth
    .join("tr")
    .call(displayLabelCell)
    .call(displaySliderCell);
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
    .attr("x", d => x(d.startValue)) // Position based on calculated start value
    .attr("width", 0) // Start with zero width for transition
    .attr("fill", (d, i) => d3.schemeTableau10[d.i % 10]) // Color based on original index
    .transition()
    .duration(750)
    .attr("width", d => Math.max(0, x(d.endValue) - x(d.startValue))); // Ensure non-negative width

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
export function initSliders() {
  // TODO: use actual data from the server
  const sliderData = [
    { id: "fat", name: "Fat", unit: "g/100g", min: 0, lower: 5, max: 100, upper: 30 },
    { id: "protein", name: "Proteins", unit: "g/100g", min: 0, lower: 10, max: 100, upper: 40 }
  ];
  const productCsv = `id,product_code,product_name,ciqual_name,ciqual_code,location,location_osm_id,quantity_g,price,protein,fat
14144,3068110702235,Farine de blé T45,"Wheat flour, type 55 (for pastry)",9440,"Intermarché, 3-5, Rue Villeneuve",246286922,357.1,0.38,30.0,3.9286
13756,3410280010311,Top budget tournesol 1l c15,Sunflower oil,17440,"Intermarché, 3-5, Rue Villeneuve",246286922,1.2,0.0,0.0,1.0714`;
  const productsData = d3.csvParse(productCsv);

  sliderData.forEach(d => (d.segments = createSegmentsData(productsData, d.id)));

  const tableBody = d3.select("#slider-table-body");
  displaySliderTable(tableBody, sliderData);
}
initSliders();
