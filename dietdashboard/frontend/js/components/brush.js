import * as d3 from "../d3";
import { handleStateChange } from "../index";

/**
 * @param {d3.Selection} parent
 * @param {Slider} d
 * @param {d3.Scale} x
 * @param {number} height
 * @param {number} width
 */
export function Brush(parent, d, x, height, width) {
  const brushHeight = 4;
  const handleRadius = 7;
  const brushSelection = d3
    .brushX()
    .extent([
      [0, height - brushHeight / 2],
      [width, height + brushHeight / 2]
    ])
    .on("brush", function (event) {
      if (!event.selection) return;
      handle.attr("transform", (d, i) => `translate(${event.selection[i]},0)`);
    })
    .on("end", function (event) {
      if (!event.sourceEvent) return;
      [d.lower, d.upper] = event.selection.map(x.invert);
      handleStateChange();
    });

  const brushGroup = parent
    .selectAll("g.brush")
    .data([d], d => d.id)
    .join(enter => enter.append("g").attr("class", "brush"))
    .call(brushSelection)
    .raise(); // Raise the brush above the segments

  const handle = brushGroup
    .selectAll("g.brush-handle")
    .data([{ type: "w" }, { type: "e" }])
    .join(enter =>
      enter
        .append("g")
        .attr("class", "brush-handle")
        .call(g => g.append("circle").attr("r", handleRadius).attr("cy", height))
    );
  brushGroup.call(brushSelection.move, [d.lower, d.upper].map(x));
}
