import * as d3 from "../d3";
import { locationStateChange } from "./locations";

/**
 * @param {d3.Selection} parent
 * @param {Array} data - location data
 * @param {object} state
 */
export function Markers(parent, data, state) {
  const projection = d3
    .geoMercator()
    .scale(1 / (2 * Math.PI))
    .translate([0, 0]);

  data.forEach(d => ([d.x, d.y] = projection([d.lon, d.lat])));

  parent
    .selectAll("circle")
    .data(data, d => d.id)
    .join("circle")
    .attr("r", 5)
    .classed("selected", d => d.id in state.locations)
    .on("click", handleMarkerClick);

  function handleMarkerClick(event, d) {
    event.stopPropagation(); // Prevent map zoom/pan on marker click
    d.id in state.locations ? delete state.locations[d.id] : (state.locations[d.id] = null);
    d3.select(this).classed("selected", d.id in state.locations);
    locationStateChange(data, state);
  }
}
