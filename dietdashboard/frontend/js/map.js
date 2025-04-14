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
  caches
    .open("locations")
    .then(
      // check if the tile is already in the cache
      // prettier-ignore
      cache => cache.match(url).then(resp => resp ? resp: fetch(url)) // cache.add(url))
    )
    .then(response => response.text())
    .then(text => csvParse(text))
    .then(data => data.forEach(point => addMarker(markersLayer, point)))
    .catch(error => console.error("Error loading tile:", error));
}

// Function that devides the current map bounding into tiles and fetches the data for each tile
// Each tile has an integer lat and lon and size of tile defined by the size variable
function refreshMarkers(markersLayer, bounds) {
  markersLayer.clearLayers();
  const { lat: latSW, lng: lonSW } = bounds.getSouthWest(),
    { lat: latNE, lng: lonNE } = bounds.getNorthEast(),
    [latS, lonS] = size,
    lanStart = Math.floor(lonSW / lonS) * lonS,
    latStart = Math.floor(latSW / latS) * latS,
    lonEnd = Math.ceil(lonNE / lonS) * lonS,
    latEnd = Math.ceil(latNE / latS) * latS;
  for (let lon = lanStart; lon <= lonEnd; lon += lonS) {
    for (let lat = latStart; lat <= latEnd; lat += latS) {
      addTileMarkers(markersLayer, lat + latS, lat, lon + lonS, lon);
    }
  }
}

function addMarker(markersLayer, { lat, lon }) {
  const marker = L.marker([lat, lon]);
  markersLayer.addLayer(marker);
}

const map = L.map("map").setView(defaultMapState.center, defaultMapState.zoom);
export function initMap() {
  L.tileLayer(osmUrl, osmTilesOptions).addTo(map); // Add OSM tiles
  const markersLayer = L.markerClusterGroup(markerClusterGroupOptions).addTo(map);
  map.on("moveend", () => refreshMarkers(markersLayer, map.getBounds()));

  // Listen for the tab becoming active, and then re-check map size
  document.getElementById("map-tab").addEventListener("change", () => map.invalidateSize());
  map.on("resize", () => map.invalidateSize());
}
