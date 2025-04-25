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

/**
 * @param {Array} products
 * @param {string} nutrientId
 */
function createSegmentsData(products, nutrientId) {
  const segments = products.map((p, i) => ({
    i: i,
    id: p.id,
    name: p.product_name,
    level: Number(p[nutrientId]) || 0
  }));
  let cum = 0;
  segments.forEach(p => {
    p.startValue = cum;
    cum += p.level;
    p.endValue = cum;
  });
  return segments;
}

/**
 * @param {d3.Selection} barGroup
 * @param {Array} segments
 * @param {d3.Scale} x
 */
function Segment(barGroup, segments, x) {
  // Setup bar positioning
  const height = CONFIG.svgHeight - CONFIG.margin.top - CONFIG.margin.bottom;
  const axisYPosition = height;
  const barYPosition = axisYPosition - CONFIG.barHeight - 2;
  const barHeight = CONFIG.barHeight; // From config
  const segmentGroups = barGroup
    .selectAll("g.segment-group")
    .data(segments, p => `${p.id}-${p.quantity_g}`)
    .join("g")
    .attr("class", "segment-group");

  // Append rectangles to entering segments (start with 0 width at final position)
  segmentGroups
    .append("rect")
    .attr("class", "segment")
    .attr("y", barYPosition)
    .attr("height", barHeight)
    .attr("x", 0)
    .attr("width", 0)
    .attr("fill", p => d3.schemeTableau10[p.i % 10])
    .transition()
    .duration(750)
    .attr("width", p => x(p.endValue) - x(p.startValue))
    .attr("x", p => x(p.startValue));

  segmentGroups
    .append("text")
    .attr("class", "segment-label")
    .attr("y", barYPosition - 5) // Position above bar
    .attr("x", d => x((d.startValue + d.endValue) / 2)) // Center based on final values
    .text(d => d.name);
}

/**
 * @param {d3.Selection} g
 * @param {object} d
 * @param {d3.Scale} x
 * @param {number} height
 * @param {number} width
 */
function Brush(g, d, x, height, width) {
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
    .selectAll(".brush-handle")
    .data([{ type: "w" }, { type: "e" }])
    .enter()
    .append("g")
    .attr("class", "brush-handle")
    .attr("cursor", "ew-resize");

  handle.append("circle").attr("r", CONFIG.handleRadius).attr("cy", height);
  brushGroup.call(brushSelection.move, [lower, upper].map(x));
}

const modal = document.getElementById("rangeModal");
const form = document.getElementById("rangeForm");
const modalTitle = document.getElementById("modalTitle");
if (!modal || !form || !modalTitle) {
  alert("Missing modal elements");
}

export function Sliders(productsData, sliderData) {
  const data = sliderData.filter(d => d.active == 1);
  data.forEach(d => (d.segments = createSegmentsData(productsData, d.id)));
  const height = CONFIG.svgHeight - CONFIG.margin.top - CONFIG.margin.bottom;
  // Local variables for each SVG element
  const x = d3.local();
  const width = d3.local();
  d3.select("#slider-table-body")
    .selectAll("tr")
    .data(data, d => d.id)
    .join(
      enter =>
        enter
          .append("tr")
          .call(tr =>
            tr
              .append("td")
              .attr("class", "slider-label")
              .append("div")
              .call(div => div.append("span").text(d => `${d.name} (${d.unit})`))
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
      // Setup local variables for each SVG element
      d3.select(this).selectAll("*").remove(); // Clear previous content TODO: update the content in a more efficient way
      const w = this.clientWidth - CONFIG.margin.left - CONFIG.margin.right;
      x.set(this, d3.scaleLinear().domain([d.min, d.max]).range([0, w]));
      width.set(this, w);
    })
    .append("g")
    .attr("transform", `translate(${CONFIG.margin.left},${CONFIG.margin.top})`)
    .each(function (d) {
      Segment(d3.select(this), d.segments, x.get(this));
    })
    .each(function (d) {
      d3.select(this)
        .append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x.get(this)).ticks(CONFIG.nTicks).tickSize(6).tickPadding(3));
    })
    .each(function (d) {
      Brush(d3.select(this), d, x.get(this), height, width.get(this));
    });
}
