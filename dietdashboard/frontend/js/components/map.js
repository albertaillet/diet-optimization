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
import { locationStateChange } from "./locations";
import { Markers } from "./markers";

const url = (x, y, z) => `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
const width = 960,
  height = 500,
  deltas = [-100, -4, -1, 0];

/**
 * @param {d3.Selection} parent
 * @param {Array<LocationInfo>} data
 * @param {State} state
 * @param {Array<Array<number>>} extent - [[x0, y0], [x1, y1]] defining the brush area
 */
function Brush(parent, data, state, extent) {
  parent.selectAll("g.map-brush").remove(); // Remove any existing brush group
  if (!state.brushMode) return; // Do not create a brush if no mode is set
  const brush = d3.brush().extent(extent).on("end", brushed);
  parent.append("g").attr("class", "map-brush").style("pointer-events", "none").call(brush);
  /**
   * @param {d3.D3BrushEvent} event
   */
  function brushed(event) {
    const currentTransform = d3.zoomTransform(parent.node()); // Get current map transform
    if (!event.selection || !state.brushMode) return;
    const [[x0, y0], [x1, y1]] = event.selection;
    data.forEach(d => {
      // d.x and d.y are base projected coordinates (from lon/lat)
      const cx = currentTransform.applyX(d.x);
      x;
      const cy = currentTransform.applyY(d.y);
      if (cx >= x0 && cx <= x1 && cy >= y0 && cy <= y1) {
        if (state.brushMode === "select") {
          state.locations[d.id] = true;
        } else if (state.brushMode === "deselect") {
          delete state.locations[d.id];
        }
      }
    });
    state.brushMode = null; // Reset brush mode after selection
    locationStateChange(data, state); // Update table, markers, controls, and brush activation state
  }
}

/**
 * @param {d3.Selection} parent
 * @param {Array<LocationInfo>} data
 * @param {State} state
 */
export function Map(parent, data, state) {
  parent.attr("viewBox", [0, 0, width, height]);

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

  const levels = parent.selectAll("g.levels").data(deltas).join("g").attr("class", "levels").attr("pointer-events", "none");

  const markerGroup = parent.selectAll("g.markers").data([null]).join("g").attr("class", "markers");
  Markers(markerGroup, data, state);

  parent
    .call(zoom)
    .call(zoom.transform, d3.zoomIdentity.translate(state.mapTransform.x, state.mapTransform.y).scale(state.mapTransform.k));

  parent.on(".zoom", state.brushMode ? null : zoom); // Disable zooming when brush mode is active

  Brush(parent, data, state, extent);

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
    persistState();
  }
}
