import { Axis } from "./components/axis";
import { Brush } from "./components/brush";
import { Segments } from "./components/segments";
import * as d3 from "./d3";
import { handleStateChange } from "./index";
// Inspired by https://observablehq.com/@sarah37/snapping-range-slider-with-d3-brush

const CONFIG = {
  margin: { top: 5, right: 20, bottom: 20, left: 10 },
  svgHeight: 50
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
    handleStateChange();
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
      Axis(slider, d, x, height);
      Segments(slider, createSegmentsData(productsData, d.id), x, height);
      Brush(slider, d, x, height, width);
    });
}
