import chroma from "chroma-js";
import L from "leaflet";
import "leaflet-draw";
import { csvParse } from "./d3";

interface LocationData {
  lat: number;
  lon: number;
  count: number;
}
const osmUrl = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const locationUrl = "/locations.csv";
const osmAttribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>';
const osmTilesOptions: L.TileLayerOptions = { maxZoom: 19, attribution: osmAttribution };
const defaultMapState = { center: [49, 10], zoom: 5 };
const drawnOptions = {
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
        interactive: true
      }
    }
  }
};

/**
 * Fetch and parse all locations from CSV, then use the provided
 * callback to add each location to the map.
 */
function fetchAndAddAllLocations(addLoc: (location: LocationData) => void): Promise<void> {
  return fetch(locationUrl)
    .then(response => response.text())
    .then(text => csvParse(text))
    .then(data => data.forEach(location => addLoc(location)))
    .catch(error => console.error("Error fetching locations:", error));
}

/**
 * Get the color for a circle representing a given count value.
 */
function getCircleColor(count: number): string {
  const colorScale = chroma.scale("RdYlGn").padding(0.15).domain([0, 50]);
  return count > 0 ? colorScale(count).hex() : "#666666";
}

/**
 * Add a location circle to the given layer with the specified renderer.
 */
function addLocation({ lat, lon, count }: LocationData, renderer: L.Canvas, locationsLayer: L.LayerGroup): void {
  const priceCount = Number(count);
  const radius = 100;
  const circleOptions = {
    renderer,
    radius,
    fillColor: getCircleColor(priceCount),
    color: "black",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.7
  };
  L.circle([lat, lon], circleOptions).bindPopup(`Price Count: ${priceCount}`).addTo(locationsLayer);
}

/**
 * Initialize draw tools (Circle tool) on the map.
 * When a new circle is created, highlights location circles
 * that fall within the drawn circle's radius.
 */
function initDrawTools(map: L.Map, locationsLayer: L.LayerGroup): void {
  const drawnItems = new L.FeatureGroup();
  map.addLayer(drawnItems);

  const drawControl = new L.Control.Draw(drawnOptions);
  map.addControl(drawControl);

  // Clear all circles when the draw button is clicked
  map.on(L.Draw.Event.DRAWSTART, () => drawnItems.clearLayers());

  // Handle the created items
  map.on(L.Draw.Event.CREATED, event => {
    const layer = event.layer;
    drawnItems.addLayer(layer);
    if (!(layer instanceof L.Circle)) return; // Only handle circles
    const center = layer.getLatLng();
    const radius = layer.getRadius();
    // Highlight circles inside the newly drawn circle
    locationsLayer.eachLayer(locationCircle => {
      const distance = center.distanceTo(locationCircle.getLatLng());
      locationCircle.setStyle(distance <= radius ? { color: "red" } : { color: "black" });
    });
  });
}

export function initMap(): void {
  const map = L.map("map").setView(defaultMapState.center, defaultMapState.zoom);
  L.tileLayer(osmUrl, osmTilesOptions).addTo(map); // Add OSM tiles
  const renderer = L.canvas({ padding: 0.5 });
  const locationsLayer = L.layerGroup().addTo(map); // Create a layer group for locations
  fetchAndAddAllLocations(location => addLocation(location, renderer, locationsLayer));
  initDrawTools(map, locationsLayer);
  document.getElementById("map-tab").addEventListener("change", () => map.invalidateSize());
  map.on("resize", () => map.invalidateSize());
}
