import { axisBottom } from "../d3";

/**
 * @param {d3.Selection} parent
 * @param {d3.Scale} x
 * @param {number} height
 */
export function Axis(parent, x, height) {
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
    .call(axisBottom(x).ticks(nTicks).tickSize(tickSize).tickPadding(tickPadding));
}
