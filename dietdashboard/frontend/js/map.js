// d3-tile for displaying raster map tiles and
// d3-zoom for panning and zooming.
// Note that unlike dedicated libraries for slippy maps such as Leaflet,
// d3-tile relies on the browser for caching and queueing,
// and thus you may see more flickering as tiles load.s
// References:
// https://observablehq.com/@d3/zoomable-tiles?collection=@d3/d3-tile
// https://observablehq.com/@d3/zoomable-map-tiles?collection=@d3/d3-tile
// https://observablehq.com/@d3/zoomable-raster-vector?collection=@d3/d3-geo
// https://observablehq.com/@d3/seamless-zoomable-map-tiles?collection=@d3/d3-tile
import * as d3 from "./d3";

const url = (x, y, z) => `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
const locationUrl = "/locations.csv";
const width = 960,
  height = 500,
  deltas = [-100, -4, -1, 0];

/**
 * @param {d3.Selection} selection
 * @param {object} state
 * @param {Array} data
 */
function Map(selection, state, data) {
  const tile = d3
    .tile()
    .extent([
      [0, 0],
      [width, height]
    ])
    .tileSize(256)
    .clampX(false);

  const zoom = d3
    .zoom()
    .scaleExtent([1 << 8, 1 << 22])
    .extent([
      [0, 0],
      [width, height]
    ])
    .on("zoom", event => zoomed(event.transform));

  const levels = selection
    .append("g")
    .attr("pointer-events", "none")
    .selectAll("g")
    .data(deltas)
    .join("g")
    .style("opacity", null);

  const markers = selection.append("g").attr("class", "markers");

  const transform = d3.zoomIdentity.translate(state.mapTransform.x, state.mapTransform.y).scale(state.mapTransform.k);

  // Add circles to the UNSELECTED group initially
  markers
    .selectAll("circle")
    .data(data, d => d.id)
    .join("circle")
    .attr("r", 5)
    .on("click", handleMarkerClick);

  selection.call(zoom).call(zoom.transform, transform);

  function handleMarkerClick(event, d) {
    event.stopPropagation(); // Prevent map zoom/pan on marker click
    state.locations.has(d.id) ? state.locations.delete(d.id) : state.locations.add(d.id, d); // Toggle selection
    d3.select(this).classed("selected", state.locations.has(d.id));
  }

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
    markers
      .selectAll("circle")
      .attr("cx", d => transform.applyX(d.x))
      .attr("cy", d => transform.applyY(d.y));
  }
}

export async function initMap(state) {
  const projection = d3
    .geoMercator()
    .scale(1 / (2 * Math.PI))
    .translate([0, 0]);

  const data = await d3.csv(locationUrl, d3.autoType);
  data.forEach(d => ([d.x, d.y] = projection([d.lon, d.lat])));

  const svg = d3.select("#map").append("svg").attr("viewBox", [0, 0, width, height]);
  Map(svg, state, data);
}
