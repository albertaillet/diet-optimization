import { select } from "../d3";
import { handleStateChange } from "../index";
import { Map } from "./map";
import { Table } from "./table";

// License attribution to https://operations.osmfoundation.org/policies/tiles/
const template = `<p style="margin: 0 0 0.5rem; font-size: 0.85rem">A map-based approach to selecting items or regions.</p>
  <div id="location-controls"></div>
  <div id="map" style="margin-top: 0.5rem"></div>
  <div class="leaflet-control-attribution leaflet-control">
  <div style="text-align: right">© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors</div>
  <table>
    <colgroup>
      <col style="width: 90%" />
      <col style="width: 10%" />
    </colgroup>
    <thead>
      <tr>
        <th>Name</th>
        <th>Count</th>
      </tr>
    </thead>
    <tbody id="location-table-body"></tbody>
  </table>
</template>`;

/**
 * @param {d3.Selection} parent
 * @param {Array<LocationInfo>} data
 * @param {State} state
 */
function LocationTable(parent, data, state) {
  const rows = data.filter(location => location.id in state.locations).map(location => [location.name, location.count]);
  Table(parent, rows);
}

/**
 * @param {Array<LocationInfo>} data
 * @param {State} state
 */
export function locationStateChange(data, state) {
  LocationTable(select("#location-table-body"), data, state);
  Map(select("#map svg"), data, state);
  handleStateChange();
}

/**
 * @param {d3.Selection} parent
 * @param {Array<LocationInfo>} data
 * @param {State} state
 */
export function Locations(parent, data, state) {
  parent.html(template);
  const svg = parent.select("#map").append("svg");
  Map(svg, data, state);
  LocationTable(parent.select("#location-table-body"), data, state);
  LocationControls(parent.select("#location-controls"), data, state);
}

/**
 * @param {d3.Selection} parent
 * @param {Array<LocationInfo>} data
 * @param {State} state
 */
function LocationControls(parent, data, state) {
  const selectAll = () => {
    data.forEach(location => (state.locations[location.id] = true));
    state.brushMode = null; // Disable brush mode
    locationStateChange(data, state);
  };
  const clearAll = () => {
    state.locations = {};
    state.brushMode = null; // Disable brush mode
    locationStateChange(data, state);
  };

  const setBrushMode = mode => {
    state.brushMode === mode ? (state.brushMode = null) : (state.brushMode = mode);
    locationStateChange(data, state);
  };

  parent
    .selectAll("button")
    .data([
      { label: "Bush", click: () => setBrushMode("select") },
      { label: "Clearing brush", click: () => setBrushMode("deselect") },
      { label: "Deactivate brush", click: () => setBrushMode(null) },
      { label: "Select All Locations", click: selectAll },
      { label: "Clear All Locations", click: clearAll }
    ])
    .join("button")
    .text(d => d.label)
    .on("click", (event, d) => d.click());
}
