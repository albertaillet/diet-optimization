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
  iconCreateFunction: iconCreateFunction,
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

function getMarkerColor(markerCount, priceCount) {
  const ratio = priceCount / markerCount;
  return ratio > 0.5 ? "dark" : ratio > 0.25 ? "#FFFF00" : "#FF0000";
  // const colorScale = chroma.scale("RdYlGn").padding(0.15).domain([0, 50]);
  // return ratio > 0 ? colorScale(ratio).hex() : "#666666";
}

function iconCreateFunction(cluster) {
  const markers = cluster.getAllChildMarkers();
  const markerCount = markers.length;
  const priceCount = markers.reduce((sum, marker) => sum + (1 || 0), 0);
  return makeIcon(markerCount, priceCount);
}

function makeIcon(markerCount, priceCount) {
  const html = `<div style="background-color:${getMarkerColor(markerCount, priceCount)};">
    <span class="marker-count">${123}</span>
    <span class="price-count">${priceCount}</span>
    </div>`;
  return L.divIcon({
    className: "custom-marker",
    html: html,
    iconSize: L.point(40, 40),
    iconAnchor: L.point(20, 20),
    popupAnchor: L.point(0, -20)
  });
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
  const marker = L.marker([lat, lon], { icon: makeIcon(1, 2), price_count: 12 });
  markersLayer.addLayer(marker);
}

// Set to record tiles that have already been loaded.
const loadedTiles = new Set();

const map = L.map("map").setView(defaultMapState.center, defaultMapState.zoom);
export function initMap() {
  L.tileLayer(osmUrl, osmTilesOptions).addTo(map); // Add OSM tiles
  const markersLayer = L.markerClusterGroup(markerClusterGroupOptions).addTo(map);
  map.on("moveend", () => addMissingMarkers(markersLayer, map.getBounds()));
  document.getElementById("map-tab").addEventListener("change", () => map.invalidateSize());
  map.on("resize", () => map.invalidateSize());
}
