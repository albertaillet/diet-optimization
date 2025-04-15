import chroma from "chroma-js";
import L from "leaflet";
import "leaflet-draw"; // Import Leaflet.Draw
import "leaflet.markercluster";
import { csvParse } from "./d3";

const osmUrl = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const locationUrl = "/locations.csv";
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

function addTileMarkers(markersLayer) {
  fetch(locationUrl)
    .then(response => response.text())
    .then(text => csvParse(text))
    .then(data => data.forEach(point => addMarker(markersLayer, point)))
    .catch(error => console.error("Error loading tile:", error));
}

function getMarkerColor(markerCount, priceCount) {
  const ratio = priceCount / markerCount;
  const colorScale = chroma.scale("RdYlGn").padding(0.15).domain([0, 50]);
  return ratio > 0 ? colorScale(ratio).hex() : "#666666";
}

function iconCreateFunction(cluster) {
  const markers = cluster.getAllChildMarkers();
  const markerCount = markers.length;
  const priceCount = markers.reduce((sum, marker) => sum + (marker.options.count || 0), 0);
  return makeIcon(markerCount, priceCount);
}

function makeIcon(markerCount, priceCount) {
  const html = `<div style="background-color:${getMarkerColor(markerCount, priceCount)};">
    <span class="marker-count">${markerCount}</span>
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

function addMarker(markersLayer, { lat, lon, count }) {
  markersLayer.addLayer(L.marker([lat, lon], { icon: makeIcon(1, Number(count)), count: Number(count) }));
}

const map = L.map("map").setView(defaultMapState.center, defaultMapState.zoom);

// Initialize drawing functionality
function initDrawTools() {
  // Create a feature group to store editable layers
  const drawnItems = new L.FeatureGroup();
  map.addLayer(drawnItems);

  // Initialize the draw control and pass it the feature group
  const drawControl = new L.Control.Draw({
    draw: {
      polyline: false,
      polygon: false,
      rectangle: false,
      marker: false,
      circlemarker: false,
      circle: {
        shapeOptions: {
          color: "#3388ff",
          fillOpacity: 0.2,
          clickable: true
        }
      }
    }
  });

  map.addControl(drawControl);

  // Handle the created items
  map.on(L.Draw.Event.CREATED, function (event) {
    const layer = event.layer;
    drawnItems.addLayer(layer);

    if (layer instanceof L.Circle) {
      const center = layer.getLatLng();
      const radius = layer.getRadius();
      console.log(`Circle created at ${center} with radius ${radius}m`);
    }
  });
}

export function initMap() {
  L.tileLayer(osmUrl, osmTilesOptions).addTo(map); // Add OSM tiles
  const markersLayer = L.markerClusterGroup(markerClusterGroupOptions).addTo(map);
  addTileMarkers(markersLayer); // Add markers to the map
  initDrawTools(); // Initialize drawing tools
  document.getElementById("map-tab").addEventListener("change", () => map.invalidateSize());
  map.on("resize", () => map.invalidateSize());
}
