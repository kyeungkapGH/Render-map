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
// they follow the same coastline the basemap draws), data/state-borders.geojson
// the province divisions only — the outer ring is stripped since the national
// outline already draws it — and data/state-labels.geojson one anchor point per
// province. See README for how the three files are regenerated.
const BORDER_COLOR = "#000000";
const STATE_BORDER_COLOR = "#555555";
const LABEL_COLOR = "#1a1a1a";

const map = new Map({
  container: "map",
  bounds: [
    [21, 8],
    [64, 53],
  ],
  fitBoundsOptions: { padding: 24 },
  // The Protomaps glyph server only carries Latin fonts, so Hangul and 州 are
  // rasterized from a local font instead.
  localIdeographFontFamily: "sans-serif",
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
      "state-labels": {
        type: "geojson",
        data: "./data/state-labels.geojson",
      },
    },
    layers: [
      // Passing no `lang` leaves the basemap's label layers out entirely, so
      // the only place names on the map are the province labels added below.
      //
      // The basemap's own admin boundary lines go too: its OSM "boundaries"
      // source-layer has no per-country identity (just an admin_level-ish
      // `kind_detail`), so it can't be filtered down to the countries we
      // draw, and leaving it in puts a second, slightly different line next
      // to each of ours.
      ...basemaps
        .layers("protomaps", basemaps.namedFlavor("light"), {})
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
      {
        id: "state-labels-text",
        type: "symbol",
        source: "state-labels",
        layout: {
          "text-field": ["get", "name"],
          "text-font": ["Noto Sans Regular"],
          "text-size": 12,
          // Every province stays labelled at every zoom, colliding labels
          // included: allow-overlap keeps this layer from being culled, and
          // ignore-placement keeps it from pushing anything else out.
          "text-allow-overlap": true,
          "text-ignore-placement": true,
        },
        paint: {
          "text-color": LABEL_COLOR,
          "text-halo-color": "#ffffff",
          "text-halo-width": 1.2,
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
