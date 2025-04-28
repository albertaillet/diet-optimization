import * as d3 from "../d3";
/**
 * @param {d3.Selection} parent
 * @param {object} d
 * @param {d3.Scale} x
 * @param {number} height
 */
export function Axis(parent, d, x, height) {
  const nTicks = 10;
  const tickSize = 6;
  const tickPadding = 3;
  parent
    .selectAll("g.axis")
    .data([x], x => x.domain())
    .join(
      enter => enter.append("g").attr("class", "axis"),
      update => update,
      exit => exit.remove()
    )
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(x).ticks(nTicks).tickSize(tickSize).tickPadding(tickPadding));
}
