import * as d3 from "../d3";

/**
 * @param {d3.Selection} parent
 * @param {object} data
 * @param {d3.Scale} x
 * @param {number} height
 */
export function Segments(parent, data, x, height) {
  const barHeight = 10;
  const barYPosition = height - barHeight - 2;
  const labelYPosition = barYPosition - 5;
  parent
    .selectAll("g.segment-group")
    .data(data, (d, i) => i)
    .join(
      enter =>
        enter
          .append("g")
          .attr("class", "segment-group")
          .call(segmentGroup => segmentGroup.append("text").attr("class", "segment-label").attr("y", labelYPosition))
          .call(
            segmentGroup =>
              segmentGroup
                .append("rect")
                .attr("class", "segment")
                .attr("y", barYPosition)
                .attr("height", barHeight)
                .attr("x", 0)
                .attr("width", 0)
                .attr("fill", p => d3.schemeTableau10[p.i % 10]) // TODO: define this in the data. Move this to after the transition
          ),
      update => update,
      exit => exit.transition().duration(100).style("opacity", 0).remove()
    )
    .transition()
    .duration(750)
    .call(segmentGroup =>
      segmentGroup
        .select("text.segment-label")
        .attr("x", d => x((d.startValue + d.endValue) / 2))
        .text(d => d.name)
    )
    .call(segmentGroup =>
      segmentGroup
        .select("rect.segment")
        .attr("x", p => x(p.startValue))
        .attr("width", p => x(p.endValue) - x(p.startValue))
    );
}
