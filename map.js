import { Map, NavigationControl, Marker, Popup, addProtocol } from "./vendor/maplibre-gl/maplibre-gl.js";

// demo-bucket.protomaps.com blocks cross-origin fetches from other sites
// (no Access-Control-Allow-Origin), so it 404s/fails silently once deployed
// even though it "works" when opened directly. Trying the Source
// Cooperative mirror instead — see README for the CORS story either way.
const PMTILES_URL = "https://data.source.coop/protomaps/openstreetmap/tiles/v4.pmtiles";

const protocol = new pmtiles.Protocol();
addProtocol("pmtiles", protocol.tile);

const SEOUL_CITY_HALL = [126.978, 37.5665];

const map = new Map({
  container: "map",
  zoom: 12,
  center: SEOUL_CITY_HALL,
  style: {
    version: 8,
    glyphs: "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf",
    sprite: "https://protomaps.github.io/basemaps-assets/sprites/v4/light",
    sources: {
      protomaps: {
        type: "vector",
        url: `pmtiles://${PMTILES_URL}`,
        attribution:
          '<a href="https://github.com/protomaps/basemaps">Protomaps</a> © <a href="https://openstreetmap.org">OpenStreetMap</a>',
      },
    },
    layers: basemaps.layers("protomaps", basemaps.namedFlavor("light"), { lang: "ko" }),
  },
});

map.addControl(new NavigationControl(), "top-right");

new Marker()
  .setLngLat(SEOUL_CITY_HALL)
  .setPopup(new Popup().setText("서울시청"))
  .addTo(map);
