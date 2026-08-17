import { Map, NavigationControl, Marker, Popup, addProtocol } from "./vendor/maplibre-gl/maplibre-gl.js";

// demo-bucket.protomaps.com blocks cross-origin fetches from other sites
// (no Access-Control-Allow-Origin), so it 404s/fails silently once deployed
// even though it "works" when opened directly. Trying the Source
// Cooperative mirror instead — see README for the CORS story either way.
const PMTILES_URL = "https://data.source.coop/protomaps/openstreetmap/v4.pmtiles";

const protocol = new pmtiles.Protocol();
addProtocol("pmtiles", protocol.tile);

const SEOUL_CITY_HALL = [126.978, 37.5665];

// data/country-borders.geojson holds the national outlines (OSM-derived, so
// they follow the same coastline the basemap draws) and
// data/state-borders.geojson the province divisions only — the outer ring is
// stripped since the national outline already draws it. See README for how
// the two files are regenerated.
const BORDER_COLOR = "#000000";
const STATE_BORDER_COLOR = "#555555";

const map = new Map({
  container: "map",
  bounds: [
    [21, 8],
    [64, 53],
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
      // Drop the basemap's own generic admin boundary lines: its OSM
      // "boundaries" source-layer has no per-country identity (just an
      // admin_level-ish `kind_detail`), so it can't be filtered down to
      // our 5 countries, and leaving it in draws a second, slightly
      // different line next to each of ours. Our GeoJSON overlay below is
      // the only border drawn.
      ...basemaps
        .layers("protomaps", basemaps.namedFlavor("light"), { lang: "ko" })
        .filter((layer) => layer.id !== "boundaries_country" && layer.id !== "boundaries"),
      {
        id: "state-borders-line",
        type: "line",
        source: "state-borders",
        paint: {
          "line-color": STATE_BORDER_COLOR,
          "line-width": 1,
          "line-dasharray": [2, 2],
        },
      },
      {
        id: "country-borders-line",
        type: "line",
        source: "country-borders",
        paint: {
          "line-color": BORDER_COLOR,
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
