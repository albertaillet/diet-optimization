import { select } from "../d3";
import { handleStateChange } from "../index";
import { Map } from "./map";
import { Markers } from "./markers";
import { Table } from "./table";

/**
 * @param {d3.Selection} parent
 * @param {Array} data - location data
 * @param {object} state
 */
export function LocationTable(parent, data, state) {
  const rows = data.filter(location => location.id in state.locations).map(location => [location.name, location.count]);
  Table(parent, rows);
}

/**
 * @param {Array} data - location data
 * @param {object} state
 */
export function locationStateChange(data, state) {
  LocationTable(select("#location-table-body"), data, state);
  Markers(select("g.markers"), data, state);
  handleStateChange();
}

/**
 * @param {Array} data - location data
 * @param {object} state
 */
export function Locations(data, state) {
  Map(select("#map"), data, state);
  LocationTable(select("#location-table-body"), data, state);
}
