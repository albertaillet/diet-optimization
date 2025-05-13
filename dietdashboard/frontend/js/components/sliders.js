import * as d3 from "../d3";
import { Axis } from "./axis";
import { Brush } from "./brush";
import { openModal } from "./rangemodal";
import { Segments } from "./segments";
// Inspired by https://observablehq.com/@sarah37/snapping-range-slider-with-d3-brush

const template = `
<p style="margin-top: 0.5rem">Adjust your nutrient targets to optimize your diet.</p>
<table style="border-spacing: 0">
  <colgroup>
    <col style="width: 15%" />
    <col style="width: 85%" />
  </colgroup>
  <tbody id="slider-table-body"></tbody>
</table>`;

const CONFIG = {
  margin: { top: 5, right: 20, bottom: 20, left: 10 },
  svgHeight: 50
};

/**
 * @param {Array} products
 * @param {string} nutrientId
 */
function createSegmentsData(products, nutrientId) {
  const segments = products.map((p, i) => ({ i: i, id: p.id, name: p.product_name, level: p[nutrientId] })).reverse();
  let cum = 0;
  segments.forEach(p => {
    p.startValue = cum;
    cum += p.level;
    p.endValue = cum;
  });
  return segments;
}

/**
 * @param {d3.Selection} parent
 * @param {Array} productsData
 * @param {Array} sliderData
 */
export function Sliders(parent, productsData, sliderData) {
  parent.html(template);
  const tableBody = parent.select("#slider-table-body");
  SlidersTableBody(tableBody, productsData, sliderData);
}

/**
 * @param {d3.Selection} parent
 * @param {Array} productsData
 * @param {Array} sliderData
 */
export function SlidersTableBody(parent, productsData, sliderData) {
  const data = sliderData.filter(d => d.active);
  const height = CONFIG.svgHeight - CONFIG.margin.top - CONFIG.margin.bottom;
  parent
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
      Axis(slider, x, height);
      Segments(slider, createSegmentsData(productsData, d.id), x, height);
      Brush(slider, d, x, height, width);
    });
}
