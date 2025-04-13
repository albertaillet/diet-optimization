import L from "leaflet";

const osmUrl = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const osmAttribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>';
const osmTilesOptions = { maxZoom: 19, attribution: osmAttribution };
const defaultMapState = { center: [49, 10], zoom: 5 };

export function initMap() {
  const map = L.map("map").setView(defaultMapState.center, defaultMapState.zoom);
  L.tileLayer(osmUrl, osmTilesOptions).addTo(map);

  // Listen for the tab becoming active, and then re-check map size
  const mapTab = document.getElementById("map-tab");
  mapTab.addEventListener("change", () => map.invalidateSize());
}
