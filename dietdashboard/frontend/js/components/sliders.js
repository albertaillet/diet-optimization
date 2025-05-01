import * as d3 from "../d3";
import { Axis } from "./axis";
import { Brush } from "./brush";
import { openModal } from "./rangemodal";
import { Segments } from "./segments";
// Inspired by https://observablehq.com/@sarah37/snapping-range-slider-with-d3-brush

const CONFIG = {
  margin: { top: 5, right: 20, bottom: 20, left: 10 },
  svgHeight: 50
};

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
