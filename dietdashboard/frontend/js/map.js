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

function map() {
  const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]);

  // Initial projection setup (used only for initial coordinate calculation)
  const projection = d3
    .geoMercator()
    .scale(1 / (2 * Math.PI))
    .translate([0, 0]);

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

  const levels = svg
    .append("g")
    .attr("class", "tiles") // Add a class for tiles group
    .attr("pointer-events", "none")
    .selectAll("g")
    .data(deltas)
    .join("g")
    .style("opacity", null);

  // Svg group for the location markers
  const markers = svg.append("g").attr("class", "markers").attr("pointer-events", "none");

  const transform = d3.zoomIdentity.translate(width >> 1, height >> 1).scale(1 << 12);

  // Load the CSV file and plot the points
  d3.csv(locationUrl)
    .then(data => {
      markers
        .selectAll("circle")
        .data(data, d => {
          // Store the *initial* projected coordinates based on the base projection
          const [x, y] = projection([+d.lon, +d.lat]);
          (d.x = x), (d.y = y);
        })
        .join("circle")
        .attr("r", 5)
        .style("fill", "red")
        .style("opacity", 0.7);

      svg.call(zoom).call(zoom.transform, transform);
    })
    .catch(error => console.error("Error loading location CSV:", error));

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

  return svg.node();
}

export function initMap() {
  const mapSvg = map();
  document.querySelector("#map").appendChild(mapSvg);
}
