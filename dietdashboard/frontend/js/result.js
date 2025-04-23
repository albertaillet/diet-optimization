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

function displayResultMacroTable(container, data) {
  const fields = ["protein", "carbohydrate", "fat"];
  if (!(data.length && fields.every(field => field in data[0]))) {
    d3.select(container).selectAll("tr").remove(); // TODO: Handle this better
    return;
  }
  const weight = Object.fromEntries(fields.map(key => [key, d3.sum(data, d => +d[key] || 0)]));
  const energy = { protein: weight.protein * 4, carbohydrate: weight.carbohydrate * 4, fat: weight.fat * 9 };
  const totalEnergy = d3.sum(Object.values(energy));
  d3.select(container)
    .selectAll("tr")
    .data([
      ["Weight", ...fields.map(field => `${weight[field].toFixed(0)}g`)],
      ["Energy", ...fields.map(field => `${energy[field].toFixed(0)} kcal`)],
      ["Percentage", ...fields.map(field => `${((energy[field] / totalEnergy) * 100).toFixed(0)}%`)]
    ])
    .join("tr")
    .selectAll("td")
    .data(d => d)
    .join("td")
    .html(d => d);
  // TODO: Pie chart
}

const currencySelector = document.getElementById("currency");
const resultTable = document.getElementById("result-table");
const resultMacroTable = document.getElementById("macro-table-body");

export function updateResult(products) {
  const totalPrice = d3.sum(products, d => +d.price || 0).toFixed(2);
  document.getElementById("result-price").innerHTML = `${totalPrice} ${currencySelector.value}`;

  displayResultTable(resultTable, products);
  displayResultMacroTable(resultMacroTable, products);
}
