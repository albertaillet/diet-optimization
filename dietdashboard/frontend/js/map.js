import L from "leaflet";
import "leaflet.markercluster";
import { csvParse } from "./d3";

const osmUrl = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const locationUrl = "/{lat_min}/{lat_max}/{lon_min}/{lon_max}/locations.csv";
const osmAttribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>';
const osmTilesOptions = { maxZoom: 19, attribution: osmAttribution };
const defaultMapState = { center: [49, 10], zoom: 5 };
const markerClusterGroupOptions = {
  showCoverageOnHover: false,
  spiderfyOnMaxZoom: false,
  removeOutsideVisibleBounds: true,
  // iconCreateFunction: iconCreateFunction,
  disableClusteringAtZoom: 15
};
const size = [10, 10]; // Size of individual fetches in degrees, lat and lon

function addTileMarkers(markersLayer, lat_max, lat_min, lon_max, lon_min) {
  const url = L.Util.template(locationUrl, { lat_min, lat_max, lon_min, lon_max });
  fetch(url)
    .then(response => response.text())
    .then(text => csvParse(text))
    .then(data => data.forEach(point => addMarker(markersLayer, point)))
    .catch(error => console.error("Error loading tile:", error));
}

// Computes the grid of tiles covering the current view and only
// loads markers for tiles not in the loadedTiles Set.
function addMissingMarkers(markersLayer, bounds) {
  const { lat: latSW, lng: lonSW } = bounds.getSouthWest(),
    { lat: latNE, lng: lonNE } = bounds.getNorthEast(),
    [latS, lonS] = size,
    lonStart = Math.floor(lonSW / lonS) * lonS,
    latStart = Math.floor(latSW / latS) * latS,
    lonEnd = Math.ceil(lonNE / lonS) * lonS,
    latEnd = Math.ceil(latNE / latS) * latS;
  for (let lon = lonStart; lon <= lonEnd; lon += lonS) {
    for (let lat = latStart; lat <= latEnd; lat += latS) {
      const tileKey = `${lat}_${lon}`;
      if (!loadedTiles.has(tileKey)) {
        addTileMarkers(markersLayer, lat + latS, lat, lon + lonS, lon);
        loadedTiles.add(tileKey);
      }
    }
  }
}

function addMarker(markersLayer, { lat, lon }) {
  const marker = L.marker([lat, lon]);
  markersLayer.addLayer(marker);
}

// Set to record tiles that have already been loaded.
const loadedTiles = new Set();

const map = L.map("map").setView(defaultMapState.center, defaultMapState.zoom);
export function initMap() {
  L.tileLayer(osmUrl, osmTilesOptions).addTo(map); // Add OSM tiles
  const markersLayer = L.layerGroup(markerClusterGroupOptions).addTo(map);
  map.on("moveend", () => addMissingMarkers(markersLayer, map.getBounds()));
  document.getElementById("map-tab").addEventListener("change", () => map.invalidateSize());
  map.on("resize", () => map.invalidateSize());
}
