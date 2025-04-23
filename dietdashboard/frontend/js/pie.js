import * as d3 from "./d3";

const DEFAULTS = {
  height: 150,
  padAngle: 0.02,
  innerRadiusRatio: 0.4,
  labelRadiusRatio: 0.7,
  colorRange: [2, 4, 8] // indices from d3.schemeTableau10
};

export function displayMacroPie(data, total, container) {
  const width = container.clientWidth;
  const { height, padAngle, innerRadiusRatio, labelRadiusRatio, colorRange } = DEFAULTS;
  const outerRadius = Math.min(width, height) / 2.8;
  const innerRadius = outerRadius * innerRadiusRatio;
  const labelRadius = outerRadius * labelRadiusRatio;

  // Create the color scale
  const color = d3
    .scaleOrdinal()
    .domain(data.map(d => d.name))
    .range(colorRange.map(i => d3.schemeTableau10[i]));

  // Create the pie layout and arc generator
  // prettier-ignore
  const pie = d3.pie().value(d => d.value).padAngle(padAngle).sort(null);
  const arc = d3.arc().innerRadius(innerRadius).outerRadius(outerRadius);
  const arcs = pie(data);

  const svg = d3
    .select(container)
    .html("")
    .append("svg")
    .attr("viewBox", [-width / 2, -height / 2, width, height]);

  // Add a sector path for each value
  svg
    .append("g")
    .attr("stroke", "white")
    .selectAll("path")
    .data(arcs)
    .join("path")
    .attr("class", "slice")
    .attr("fill", d => color(d.data.name))
    .attr("d", arc);

  // Add labels
  const arcLabel = d3.arc().innerRadius(labelRadius).outerRadius(labelRadius);
  svg
    .append("g")
    .attr("text-anchor", "middle")
    .selectAll("text")
    .data(arcs)
    .join("text")
    .attr("class", "pie-label")
    .attr("transform", d => `translate(${arcLabel.centroid(d)})`)
    .call(text => text.text(d => d.data.name));

  // Center text
  svg.append("text").attr("text-anchor", "middle").attr("dy", "0em").text(total.toFixed(0));
  svg.append("text").attr("text-anchor", "middle").attr("dy", "1.2em").text("kcal");
}
