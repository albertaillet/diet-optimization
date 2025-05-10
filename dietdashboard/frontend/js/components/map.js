// d3-tile for displaying raster map tiles and
// d3-zoom for panning and zooming.
// Note that unlike dedicated libraries for slippy maps such as Leaflet,
// d3-tile relies on the browser for caching and queueing,
// and thus you may see more flickering as tiles load.
// References:
// https://observablehq.com/@d3/zoomable-tiles?collection=@d3/d3-tile
// https://observablehq.com/@d3/zoomable-map-tiles?collection=@d3/d3-tile
// https://observablehq.com/@d3/zoomable-raster-vector?collection=@d3/d3-geo
// https://observablehq.com/@d3/seamless-zoomable-map-tiles?collection=@d3/d3-tile
import * as d3 from "../d3";
import { persistState } from "../index";
import { Markers } from "./markers";

const url = (x, y, z) => `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
const width = 960,
  height = 500,
  deltas = [-100, -4, -1, 0];

/**
 * @param {d3.Selection} parent
 * @param {Array} data
 * @param {object} state
 */
export function Map(parent, data, state) {
  const svg = parent.append("svg").attr("viewBox", [0, 0, width, height]);

  const extent = [
    [0, 0],
    [width, height]
  ];
  const tile = d3.tile().extent(extent).tileSize(256).clampX(false);

  const zoom = d3
    .zoom()
    .scaleExtent([1 << 8, 1 << 22])
    .extent(extent)
    .on("zoom", event => zoomed(event.transform));

  const levels = svg.append("g").attr("pointer-events", "none").selectAll("g").data(deltas).join("g").style("opacity", null);

  const markerGroup = svg.append("g").attr("class", "markers");

  const transform = d3.zoomIdentity.translate(state.mapTransform.x, state.mapTransform.y).scale(state.mapTransform.k);

  // Brush overlay for rectangular selection (uncomment to enable)
  // const brush = d3.brush().extent(extent).on("end", brushed);
  // svg.append("g").attr("class", "brush").call(brush);

  Markers(markerGroup, data, state);

  svg
    .call(zoom)
    // .on("dblclick.zoom", null)
    // .on("mousedown.zoom", null)
    // .on("touchstart.zoom", null)
    .call(zoom.transform, transform);

  function zoomed(transform) {
    // Update all tile levels based on the current transform
    levels.each(function (delta) {
      const tiles = tile.zoomDelta(delta)(transform);
      d3.select(this)
        .selectAll("image")
        .data(tiles, d => d)
        .join("image")
        .attr("xlink:href", d => url(...d3.tileWrap(d)))
        .attr("x", ([x]) => (x + tiles.translate[0]) * tiles.scale)
        .attr("y", ([, y]) => (y + tiles.translate[1]) * tiles.scale)
        .attr("width", tiles.scale)
        .attr("height", tiles.scale);
    });

    // Update marker positions
    markerGroup
      .selectAll("circle")
      .attr("cx", d => transform.applyX(d.x))
      .attr("cy", d => transform.applyY(d.y));
    state.mapTransform = { k: transform.k, x: transform.x, y: transform.y };
    persistState(state);
  }

  /**
   * @param {d3.Event}
   */
  function brushed(event) {
    if (!event.selection) return;
    const [[x0, y0], [x1, y1]] = event.selection;

    data.forEach(d => {
      const cx = transform.applyX(d.x);
      const cy = transform.applyY(d.y);
      if (cx >= x0 && cx <= x1 && cy >= y0 && cy <= y1) {
        state.locations[d.id] = null;
      }
    });

    svg.select(".brush").call(brush.move, null);
  }
}
