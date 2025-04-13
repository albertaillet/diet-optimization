import L from "leaflet";
import { csvParse } from "./d3";

const LocationGridLayer = L.GridLayer.extend({
  initialize: function (url, options) {
    L.GridLayer.prototype.initialize.call(this, options); // Call parent initializer
    this._markerLayer = options.markerLayer; // Assume markerLayer is provided as an option: a L.LayerGroup for markers.
    this._url = url; // URL template for fetching CSV data.
  },

  // Define how to create each tile.
  _addTile: function (coords, container) {
    const url = L.Util.template(this._url, coords); // Create the URL, replacing placeholders with tile coordinates.
    fetch(url, { method: "GET" }) // Make sure that this URL has cache-control headers set to allow caching.
      .then(response => response.text())
      .then(text => csvParse(text))
      .then(data => this._addMarkers(data))
      .catch(error => console.error("Error loading tile:", error));
  },

  // Add markers from CSV data to the marker layer.
  _addMarkers: function (data) {
    data.forEach(function (point) {
      const lat = parseFloat(point.lat);
      const lon = parseFloat(point.lon);
      if (!isNaN(lat) && !isNaN(lon)) {
        const marker = L.marker([lat, lon]);
        marker.bindPopup("Marker at: " + lat + ", " + lon); // Add popups or additional styling here.
        this._markerLayer.addLayer(marker); // Add the marker to the marker layer.
      }
    }, this);
  }
});

const osmUrl = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const locationUrl = "/{z}/{x}/{y}/locations.csv";
const osmAttribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>';
const osmTilesOptions = { maxZoom: 19, attribution: osmAttribution };
const defaultMapState = { center: [49, 10], zoom: 5 };

export function initMap() {
  const map = L.map("map").setView(defaultMapState.center, defaultMapState.zoom);
  L.tileLayer(osmUrl, osmTilesOptions).addTo(map);
  var markerLayer = L.layerGroup().addTo(map);
  var csvTileLayer = new LocationGridLayer(locationUrl, { markerLayer: markerLayer });
  map.addLayer(csvTileLayer);

  // Listen for the tab becoming active, and then re-check map size
  document.getElementById("map-tab").addEventListener("change", () => map.invalidateSize());
}
