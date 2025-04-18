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

function fetchAndAddAllLocations(addLocation) {
  return fetch(locationUrl)
    .then(response => response.text())
    .then(text => d3.csvParse(text))
    .then(data => data.forEach(location => addLocation(location)))
    .catch(error => console.error("Error fetching locations:", error));
}

function map() {
  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]);

  const tile = d3
    .tile()
    .extent([
      [0, 0],
      [width, height]
    ])
    .tileSize(512)
    .clampX(false);

  const zoom = d3
    .zoom()
    .scaleExtent([1 << 8, 1 << 22])
    .extent([
      [0, 0],
      [width, height]
    ])
    .on("zoom", event => zoomed(event.transform));

  const levels = svg.append("g").attr("pointer-events", "none").selectAll("g").data(deltas).join("g").style("opacity", null);

  const transform = d3.zoomIdentity.translate(width >> 1, height >> 1).scale(1 << 12);

  svg.call(zoom).call(zoom.transform, transform);

  function zoomed(transform) {
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
  }
  return svg.node();
}

export function initMap() {
  const mapSvg = map();
  document.querySelector("#map").appendChild(mapSvg);
}
