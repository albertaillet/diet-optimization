import * as d3 from "./d3";

const rowData = product => [
  { text: product.product_name, link: `https://world.openfoodfacts.org/product/${product.product_code}` },
  { text: product.ciqual_name, link: `https://ciqual.anses.fr/#/aliments/${product.ciqual_code}` },
  { text: product.location, link: `https://www.openstreetmap.org/way/${product.location_osm_id}` },
  { text: product.quantity_g, link: `info/${product.id}` },
  { text: product.price, link: `https://prices.openfoodfacts.org/prices/${product.id}` }
];

function displayResultTable(container, data) {
  const rows = d3
    .select(container)
    .selectAll("tr")
    .data(data, d => d.id);
  rows.exit().remove();
  rows
    .enter()
    .append("tr")
    .selectAll("td")
    .data(d => rowData(d))
    .enter()
    .append("td")
    .html(d => `<a href="${d.link}" target="_blank">${d.text}</a>`);
}

const currencySelector = document.getElementById("currency");
const resultTable = document.getElementById("result-table");
const resultSummary = d3.select("#result-summary");

export function updateResult(products) {
  const totalPrice = d3.sum(products, d => +d.price || 0).toFixed(2);
  document.getElementById("result-price").innerHTML = `${totalPrice} ${currencySelector.value}`;

  displayResultTable(resultTable, products);
  // TODO: displayResultSummary(resultSummary, products);
}
