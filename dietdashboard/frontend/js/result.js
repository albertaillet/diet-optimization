import * as d3 from "./d3";

function displayResultTable(container, data) {
  d3.select(container)
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

const currencySelector = document.getElementById("currency");
const resultTable = document.getElementById("result-table");
const resultSummary = d3.select("#result-summary");

export function updateResult(products) {
  const totalPrice = d3.sum(products, d => +d.price || 0).toFixed(2);
  document.getElementById("result-price").innerHTML = `${totalPrice} ${currencySelector.value}`;

  displayResultTable(resultTable, products);
  // TODO: displayResultSummary(resultSummary, products);
}
