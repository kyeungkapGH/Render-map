import { Map, NavigationControl, Marker, Popup, addProtocol } from "./vendor/maplibre-gl/maplibre-gl.js";

// demo-bucket.protomaps.com blocks cross-origin fetches from other sites
// (no Access-Control-Allow-Origin), so it 404s/fails silently once deployed
// even though it "works" when opened directly. Trying the Source
// Cooperative mirror instead — see README for the CORS story either way.
const PMTILES_URL = "https://data.source.coop/protomaps/openstreetmap/v4.pmtiles";

const protocol = new pmtiles.Protocol();
addProtocol("pmtiles", protocol.tile);

const SEOUL_CITY_HALL = [126.978, 37.5665];

// ISO 3166-1 alpha-3 codes, matched against the `iso_a3` /
// `country_iso_a3` properties in data/country-borders.geojson and
// data/state-borders.geojson (both filtered from Natural Earth's public
// domain admin-0 / admin-1 datasets down to just these countries).
const COUNTRY_COLORS = {
  UKR: "#4c72b0",
  LBN: "#dd8452",
  ISR: "#55a868",
  YEM: "#c44e52",
  IRN: "#8172b3",
};
const countryColorMatch = ["match", ["get", "iso_a3"], ...Object.entries(COUNTRY_COLORS).flat(), "#999999"];
const stateColorMatch = ["match", ["get", "country_iso_a3"], ...Object.entries(COUNTRY_COLORS).flat(), "#999999"];

const map = new Map({
  container: "map",
  bounds: [
    [20, 10],
    [65, 55],
  ],
  fitBoundsOptions: { padding: 24 },
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
      "country-borders": {
        type: "geojson",
        data: "./data/country-borders.geojson",
      },
      "state-borders": {
        type: "geojson",
        data: "./data/state-borders.geojson",
      },
    },
    layers: [
      ...basemaps.layers("protomaps", basemaps.namedFlavor("light"), { lang: "ko" }),
      {
        id: "state-borders-line",
        type: "line",
        source: "state-borders",
        paint: {
          "line-color": stateColorMatch,
          "line-width": 1,
          "line-dasharray": [2, 2],
          "line-opacity": 0.8,
        },
      },
      {
        id: "country-borders-line",
        type: "line",
        source: "country-borders",
        paint: {
          "line-color": countryColorMatch,
          "line-width": 2.5,
        },
      },
    ],
  },
});

map.addControl(new NavigationControl(), "top-right");

new Marker()
  .setLngLat(SEOUL_CITY_HALL)
  .setPopup(new Popup().setText("서울시청"))
  .addTo(map);
