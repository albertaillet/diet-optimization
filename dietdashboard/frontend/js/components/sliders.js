import * as d3 from "../d3";
import { handleStateChange } from "../index";
import { Axis } from "./axis";
import { Brush } from "./brush";
import { openModal } from "./rangemodal";
import { Segments } from "./segments";
// Inspired by https://observablehq.com/@sarah37/snapping-range-slider-with-d3-brush

const template = `
<p style="margin-top: 0.5rem">Adjust your nutrient targets to optimize your diet.</p>
<table style="border-spacing: 0" id="slider-table-body">
  <colgroup>
    <col style="width: 15%" />
    <col style="width: 1%" />
    <col style="width: 10%" />
    <col style="width: 80%" />
  </colgroup>
</table>`;

const CONFIG = {
  margin: { top: 5, right: 20, bottom: 20, left: 10 },
  svgHeight: 50
};

const NUTRIENTTYPES = ["energy", "macro", "sugar", "fatty_acid", "mineral", "vitamin", "other"];
const NUTRIENTTYPENAMES = {
  energy: "Energy",
  macro: "Macronutrients",
  sugar: "Sugar",
  fatty_acid: "Fatty Acids",
  mineral: "Minerals",
  vitamin: "Vitamins",
  other: "Other Nutrients"
};

/**
 * @param {d3.Selection} parent
 * @param {Array<Result>} productsData
 * @param {Array<Slider>} sliderData
 */
export function Sliders(parent, productsData, sliderData) {
  parent.html(template);
  const tableBody = parent.select("#slider-table-body");
  SlidersTableBody(tableBody, productsData, sliderData);
}

/**
 * @param {d3.Selection} parent
 */
function SliderLabelAndButtons(parent) {
  /**
   * @param {string} nutrient_type
   * @param {boolean} bool
   */
  const setAllCheckboxes = (nutrient_type, bool) =>
    parent
      .selectAll("input[type='checkbox']")
      .filter(d => d.nutrient_type == nutrient_type)
      .property("checked", bool)
      .each(d => (d.active = bool));

  // Add header row
  parent
    .filter(d => d.header)
    .append("td")
    .attr("colspan", 4)
    .append("div")
    .attr("style", "display: flex; justify-content: space-between; align-items: center;")
    .call(div => div.append("h3").text(d => NUTRIENTTYPENAMES[d.nutrient_type]))
    .append("div")
    .call(div => {
      div
        .append("button")
        .text("Deselect All")
        .on("click", (event, d) => {
          setAllCheckboxes(d.nutrient_type, false);
          handleStateChange();
        });
      div
        .append("button")
        .text("Select All")
        .on("click", (event, d) => {
          setAllCheckboxes(d.nutrient_type, true);
          handleStateChange();
        });
    });

  // Add nutrient rows with sliders
  parent
    .filter(d => !d.header)
    .call(tr => tr.append("td").text(d => `${d.name} (${d.unit})`))
    .call(tr =>
      tr
        .append("td")
        .append("input")
        .attr("type", "checkbox")
        .property("checked", d => d.active)
        .on("change", (event, d) => {
          d.active = event.target.checked;
          handleStateChange();
        })
    )
    .call(tr => tr.append("td").append("button").text("Edit Range").on("click", openModal))
    .append("td")
    .append("svg")
    .attr("width", "100%")
    .attr("height", CONFIG.svgHeight)
    .append("g")
    .attr("class", "slider")
    .attr("transform", `translate(${CONFIG.margin.left},${CONFIG.margin.top})`);
}

/**
 * @param {d3.Selection} parent
 * @param {Array<Result>} productsData
 * @param {Array<Slider>} sliderData
 */
export function SlidersTableBody(parent, productsData, sliderData) {
  const height = CONFIG.svgHeight - CONFIG.margin.top - CONFIG.margin.bottom;
  parent
    .selectAll("tbody")
    .data(NUTRIENTTYPES, d => d)
    .join("tbody")
    .selectAll("tr")
    .data(
      d => [
        { header: true, nutrient_type: d, id: `nutrient_${d}` },
        ...sliderData.filter(nutrient => nutrient.nutrient_type == d)
      ],
      d => d.id
    )
    .join(enter => enter.append("tr").call(SliderLabelAndButtons))
    .select("svg")
    .select("g.slider")
    .each(function (d) {
      const slider = d3.select(this);
      if (!d.active || d.header) {
        slider.selectAll("*").remove();
        return;
      }
      const width = this.parentNode.clientWidth - CONFIG.margin.left - CONFIG.margin.right;
      const x = d3.scaleLinear().domain([d.min, d.max]).range([0, width]);
      Axis(slider, x, height);
      Segments(slider, productsData, d.id, x, height);
      Brush(slider, d, x, height, width);
    });
}
