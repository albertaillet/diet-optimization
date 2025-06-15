import * as d3 from "../d3";
// console.log(d3.schemeTableau10);

/**
 * @param {Array<Result>} products
 * @param {string} nutrientId
 */
function createSegmentsData(products, nutrientId) {
  const segments = products
    .map((p, i) => ({ i: i, id: p.id, name: p.product_name, level: p[nutrientId], color: p.color }))
    .reverse();
  let cum = 0;
  segments.forEach(p => {
    p.startValue = cum;
    cum += p.level;
    p.endValue = cum;
  });
  return segments;
}

/**
 * @param {d3.Selection} parent
 * @param {object} data
 * @param {string} id - nutrient id
 * @param {d3.Scale} x
 * @param {number} height
 */
export function Segments(parent, productsData, id, x, height) {
  const data = createSegmentsData(productsData, id);
  const barHeight = 10;
  const barYPosition = height - barHeight - 2;
  const labelYPosition = barYPosition - 5;
  parent
    .selectAll("g.segment-group")
    .data(data, (d, i) => d.id)
    .join(
      enter =>
        enter
          .append("g")
          .attr("class", "segment-group")
          .call(segmentGroup => segmentGroup.append("text").attr("class", "segment-label").attr("y", labelYPosition))
          .call(segmentGroup =>
            segmentGroup
              .append("rect")
              .attr("class", "segment")
              .attr("y", barYPosition)
              .attr("height", barHeight)
              .attr("x", 0)
              .attr("width", 0)
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
        .attr("fill", p => p.color)
    );
}
