const SEOUL_CITY_HALL = [37.5665, 126.9780];

const map = L.map("map").setView(SEOUL_CITY_HALL, 13);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
  maxZoom: 19,
}).addTo(map);

L.marker(SEOUL_CITY_HALL)
  .addTo(map)
  .bindPopup("서울시청")
  .openPopup();
