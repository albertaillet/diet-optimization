import * as d3 from "../d3";
import { MacroPie } from "./pie";
import { Table } from "./table";
/**
 * @param {d3.Selection} parent
 * @param {Array} data
 */
function ResultTable(parent, data) {
  parent
    .selectAll("tr")
    .data(data, d => d.id)
    .join("tr")
    .selectAll("td")
    .data(d => [
      { text: d.product_name, link: `https://world.openfoodfacts.org/product/${d.product_code}` },
      { text: d.ciqual_name, link: `https://ciqual.anses.fr/#/aliments/${d.ciqual_code}` },
      { text: d.location, link: `https://www.openstreetmap.org/way/${d.location_osm_id}` },
      { text: d.quantity_g, link: `info/${d.id}` },
      { text: d.price, link: `https://prices.openfoodfacts.org/prices/${d.id}` }
    ])
    .join("td")
    .html(d => `<a href="${d.link}" target="_blank">${d.text}</a>`);
}

/**
 * @param {d3.Selection} tableContainer
 * @param {d3.Selection} pieContainer
 * @param {Array} data
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

const resultTable = d3.select("#result-table");
const macroTable = d3.select("#macro-table-body");
const macroPie = d3.select("#macro-pie");
if (!resultTable || !macroTable || !macroPie) {
  alert("Missing result table or macro table or macro pie");
}

export function Result(products, currency) {
  const totalPrice = d3.sum(products, d => +d.price || 0).toFixed(2);
  document.getElementById("result-price").innerHTML = `${totalPrice} ${currency}`;

  ResultTable(resultTable, products);
  MacroSummary(macroTable, macroPie, products);
}
