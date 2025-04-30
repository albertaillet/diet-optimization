/**
 * @param {d3.Selection} parent
 * @param {Array} data
 */
export function Table(parent, data) {
  parent
    .selectAll("tr")
    .data(data)
    .join("tr")
    .selectAll("td")
    .data(d => d)
    .join("td")
    .html(d => d);
}
