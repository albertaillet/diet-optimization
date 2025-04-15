import chroma from "chroma-js";
import L from "leaflet";
import "leaflet-draw";
import { csvParse } from "./d3";

const osmUrl = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const locationUrl = "/locations.csv";
const osmAttribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>';
const osmTilesOptions = { maxZoom: 19, attribution: osmAttribution };
const defaultMapState = { center: [49, 10], zoom: 5 };

function fetchAndAddAllLocations(addLocation) {
  return fetch(locationUrl)
    .then(response => response.text())
    .then(text => csvParse(text))
    .then(data => data.forEach(location => addLocation(location)))
    .catch(error => console.error("Error fetching locations:", error));
}

function getCircleColor(count) {
  const colorScale = chroma.scale("RdYlGn").padding(0.15).domain([0, 50]);
  return count > 0 ? colorScale(count).hex() : "#666666";
}

function addLocation({ lat, lon, count }, renderer, layer) {
  const priceCount = Number(count);
  const radius = 100;
  const circleOptions = {
    renderer: renderer,
    radius: radius,
    fillColor: getCircleColor(priceCount),
    color: "black",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.7
  };
  L.circle([lat, lon], circleOptions).bindPopup(`Price Count: ${priceCount}`).addTo(layer);
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

  // Clear all circles when the draw button is clicked
  document.querySelector(".leaflet-draw-draw-circle").addEventListener("click", () => drawnItems.clearLayers());

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
  const renderer = L.canvas({ padding: 0.5 });
  const locationsLayer = L.layerGroup().addTo(map); // Create a layer group for locations
  fetchAndAddAllLocations(location => addLocation(location, renderer, locationsLayer));
  initDrawTools(); // Initialize drawing tools
  document.getElementById("map-tab").addEventListener("change", () => map.invalidateSize());
  map.on("resize", () => map.invalidateSize());
}
