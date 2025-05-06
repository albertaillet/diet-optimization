import { select } from "../d3";
import { Map } from "./map";
import { Table } from "./table";

/**
 * @param {Array} data - location data
 * @param {object} state
 */
export function Locations(data, state) {
  Map(select("#map"), data, state);
  const rows = data.filter(location => location.id in state.locations).map(location => [location.name, location.count]);
  Table(select("#location-table-body"), rows);
}
