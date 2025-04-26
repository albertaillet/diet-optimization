import * as d3 from "./d3";
import { optimize } from "./index";
// Inspired by https://observablehq.com/@sarah37/snapping-range-slider-with-d3-brush

// Common configuration values
const CONFIG = {
  margin: { top: 5, right: 20, bottom: 20, left: 10 },
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
    const btn = event.submitter || document.activeElement;
    if (btn.name !== "save") return;
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
  const segments = products
    .map((p, i) => ({ i: i, id: p.id, name: p.product_name, level: Number(p[nutrientId]) || 0 }))
    .reverse();
  let cum = 0;
  segments.forEach(p => {
    p.startValue = cum;
    cum += p.level;
    p.endValue = cum;
  });
  return segments;
}

/**
 * @param {d3.Selection} slider
 * @param {d3.Scale} x
 * @param {Array} segments
 * @param {number} height
 */
function Segments(slider, x, segments, height) {
  const barYPosition = height - CONFIG.barHeight - 2;
  const barHeight = CONFIG.barHeight; // From config
  const labelYPosition = barYPosition - 5;
  slider
    .selectAll("g.segment-group")
    .data(segments, (d, i) => i)
    .join(
      enter =>
        enter
          .append("g")
          .attr("class", "segment-group")
          .call(segmentGroup => segmentGroup.append("text").attr("class", "segment-label").attr("y", labelYPosition))
          .call(
            segmentGroup =>
              segmentGroup
                .append("rect")
                .attr("class", "segment")
                .attr("y", barYPosition)
                .attr("height", barHeight)
                .attr("x", 0)
                .attr("width", 0)
                .attr("fill", p => d3.schemeTableau10[p.i % 10]) // TODO: define this in the data.
          ),
      update => update,
      exit => exit.transition().duration(100).style("opacity", 0).remove()
    )
    .transition()
    .duration(750)
    .call(segmentGroup =>
      segmentGroup
        .select("text.segment-label")
        .attr("x", d => x((d.startValue + d.endValue) / 2))
        .text(d => d.name)
    )
    .call(segmentGroup =>
      segmentGroup
        .select("rect.segment")
        .attr("x", p => x(p.startValue))
        .attr("width", p => x(p.endValue) - x(p.startValue))
    );
}

/**
 * @param {d3.Selection} slider
 * @param {d3.Scale} x
 * @param {object} d
 * @param {number} height
 * @param {number} width
 */
function Brush(slider, x, d, height, width) {
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

  const brushGroup = slider
    .selectAll("g.brush")
    .data([d], d => d.id)
    .join(
      enter => enter.append("g").attr("class", "brush"),
      update => update,
      exit => exit.remove()
    )
    .call(brushSelection)
    .raise(); // Raise the brush above the segments

  const handle = brushGroup
    .selectAll("g.brush-handle")
    .data([{ type: "w" }, { type: "e" }])
    .join(enter =>
      enter
        .append("g")
        .attr("class", "brush-handle")
        .call(g => g.append("circle").attr("r", CONFIG.handleRadius).attr("cy", height))
    );
  brushGroup.call(brushSelection.move, [d.lower, d.upper].map(x));
}

/**
 * @param {d3.Selection} slider
 * @param {d3.Scale} x
 * @param {object} d
 * @param {number} height
 */
function Axis(slider, x, d, height) {
  slider
    .selectAll("g.axis")
    .data([d], d => d.id)
    .join(
      enter => enter.append("g").attr("class", "axis").attr("transform", `translate(0,${height})`),
      update => update,
      exit => exit.remove()
    )
    .call(d3.axisBottom(x).ticks(CONFIG.nTicks).tickSize(6).tickPadding(3));
}

const modal = document.getElementById("rangeModal");
const form = document.getElementById("rangeForm");
const modalTitle = document.getElementById("modalTitle");
if (!modal || !form || !modalTitle) {
  alert("Missing modal elements");
}

export function Sliders(productsData, sliderData) {
  const data = sliderData.filter(d => d.active);
  const height = CONFIG.svgHeight - CONFIG.margin.top - CONFIG.margin.bottom;
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
          .attr("height", CONFIG.svgHeight)
          .append("g")
          .attr("class", "slider")
          .attr("transform", `translate(${CONFIG.margin.left},${CONFIG.margin.top})`),
      update => update.select("svg").select("g.slider"),
      exit => exit.remove()
    )
    .each(function (d) {
      const slider = d3.select(this);
      const width = this.parentNode.clientWidth - CONFIG.margin.left - CONFIG.margin.right;
      const x = d3.scaleLinear().domain([d.min, d.max]).range([0, width]);
      Axis(slider, x, d, height);
      Segments(slider, x, createSegmentsData(productsData, d.id), height);
      Brush(slider, x, d, height, width);
    });
}
