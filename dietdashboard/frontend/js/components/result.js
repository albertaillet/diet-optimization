import * as d3 from "../d3";
import { MacroPie } from "./pie";
import { Table } from "./table";

const template = `<p>The recommended food items and quantities to meet your nutrient targets.</p>
<h3>Total price per day: <span id="result-price"></span></h3>
<div style="display: flex; flex-direction: row; justify-content: center; align-items: center">
  <div id="macro-pie" style="flex: 1"></div>
  <div style="flex: 1; margin: 30px; width: 60%">
    <h3>Macronutrient breakdown</h3>
    <table>
      <colgroup>
        <col style="width: 25%" />
        <col style="width: 25%" />
        <col style="width: 25%" />
        <col style="width: 25%" />
      </colgroup>
      <thead>
        <tr>
          <th></th>
          <th>Protein</th>
          <th>Carbs</th>
          <th>Fat</th>
        </tr>
      </thead>
      <tbody id="macro-table-body"></tbody>
    </table>
  </div>
</div>
<div>
  <table>
    <colgroup>
      <col style="width: 25%" />
      <col style="width: 25%" />
      <col style="width: 20%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
    </colgroup>
    <thead>
      <tr>
        <th>Product name</th>
        <th>Ciqual Name</th>
        <th>Location</th>
        <th>Quantity (g)</th>
        <th>Price</th>
        <th></th>
      </tr>
    </thead>
    <tbody id="result-table"></tbody>
  </table>
</div>`;

/**
 * @param {d3.Selection} parent
 * @param {Array<Result>} data
 */
function ResultTable(parent, data) {
  Table(
    parent,
    data.map(d => [
      `<a href="https://world.openfoodfacts.org/product/${d.product_code}" target="_blank">${d.product_name}</a>`,
      `<a href="https://ciqual.anses.fr/#/aliments/${d.ciqual_code}" target="_blank">${d.ciqual_name}</a>`,
      `<a href="https://www.openstreetmap.org/way/${d.location_osm_id}" target="_blank">${d.location}</a>`,
      `${d.quantity_g}`,
      `<a href="https://prices.openfoodfacts.org/prices/${d.id}" target="_blank">${d.price}</a>`,
      `<a href="info/${d.id}" target="_blank">Product Info</a>`
    ])
  );
}

/**
 * @param {d3.Selection} tableContainer
 * @param {d3.Selection} pieContainer
 * @param {Array<Result>} data
 */
function MacroSummary(tableContainer, pieContainer, data) {
  const fields = ["protein", "carbohydrate", "fat"];
  if (!(data.length && fields.every(field => field in data[0]))) {
    tableContainer.selectAll("tr").remove(); // TODO: Handle this better
    pieContainer.selectAll("svg").remove();
    return;
  }
  const weight = Object.fromEntries(fields.map(key => [key, d3.sum(data, d => +d[key] || 0)]));
  const energy = { protein: weight.protein * 4, carbohydrate: weight.carbohydrate * 4, fat: weight.fat * 9 };
  const totalEnergy = d3.sum(Object.values(energy));
  Table(tableContainer, [
    ["Weight", ...fields.map(field => `${weight[field].toFixed(0)}g`)],
    ["Energy", ...fields.map(field => `${energy[field].toFixed(0)} kcal`)],
    ["Percentage", ...fields.map(field => `${((energy[field] / totalEnergy) * 100).toFixed(0)}%`)]
  ]);
  MacroPie(
    pieContainer,
    fields.map(field => ({ name: field, value: energy[field] })),
    totalEnergy
  );
}

/**
 * @param {d3.Selection} parent
 * @param {Array<Result>} resultData
 */
export function Result(parent, resultData) {
  parent.html(template);
  const totalPrice = d3.sum(resultData, d => +d.price || 0).toFixed(2);
  parent.select("#result-price").text(`${totalPrice} EUR`);
  ResultTable(parent.select("#result-table"), resultData);
  MacroSummary(parent.select("#macro-table-body"), parent.select("#macro-pie"), resultData);
}
