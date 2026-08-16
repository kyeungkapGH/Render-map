#!/usr/bin/env python3
"""Regenerate data/country-borders.geojson and data/state-borders.geojson.

Why two different sources:

* National outlines come from @geo-maps/countries-land, which is derived from
  OpenStreetMap and already clipped to the OSM coastline. That matters because
  the basemap is OSM-derived too, so the borders land on the same coastline the
  map draws. Natural Earth's outlines are generalized to a ~1:10m scale and
  visibly drift away from the basemap along the coast.
* Province divisions come from Natural Earth's admin-1 set, since there is no
  equally convenient OSM-lineage province dataset. Each province is clipped to
  its country's OSM polygon, then the ring that coincides with the national
  border is stripped — so only the interior divisions are written out, and
  nothing is drawn twice. Interior divisions have no basemap counterpart to
  disagree with, so their coarser lineage does not show.

Usage:
    pip install shapely
    npm install @geo-maps/countries-land-100m
    curl -O https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
    python3 scripts/build-borders.py

To change which countries are drawn, edit TARGET/NAMES below and add matching
entries to COUNTRY_COLORS in map.js.
"""

import json
from pathlib import Path

from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.ops import linemerge, unary_union
from shapely.validation import make_valid

TARGET = {"UKR", "LBN", "ISR", "YEM", "IRN"}
NAMES = {
    "UKR": "Ukraine",
    "LBN": "Lebanon",
    "ISR": "Israel",
    "YEM": "Yemen",
    "IRN": "Iran",
}

COUNTRIES_LAND = Path("node_modules/@geo-maps/countries-land-100m/map.geo.json")
ADMIN1 = Path("ne_10m_admin_1_states_provinces.geojson")
OUT_DIR = Path("data")

# Drop islets below ~1 km2. They are invisible at the zooms this map uses and
# make up a large share of the vertex count.
MIN_AREA = 1e-4
# ~200m. Wide enough to swallow the national border ring when subtracting it
# from the province rings, narrow enough to keep real interior divisions.
BORDER_EPS = 0.002
# ~1m of precision, which is finer than the source data resolves.
PRECISION = 5


def clean(geom):
    if not geom.is_valid:
        geom = make_valid(geom)
    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        if polys:
            geom = unary_union(polys)
    return geom


def fill_holes(geom):
    """Keep exterior rings only.

    countries-land carves inland lakes out of the land polygon, and those holes
    would otherwise be stroked as if they were borders.
    """
    polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    kept = [clean(Polygon(p.exterior)) for p in polys if Polygon(p.exterior).area >= MIN_AREA]
    return clean(unary_union(kept))


def round_coords(obj):
    if isinstance(obj, float):
        return round(obj, PRECISION)
    if isinstance(obj, (list, tuple)):
        return [round_coords(x) for x in obj]
    return obj


def main():
    countries = {}
    for feature in json.loads(COUNTRIES_LAND.read_text())["features"]:
        iso = feature["properties"].get("A3")
        if iso in TARGET:
            countries[iso] = fill_holes(clean(shape(feature["geometry"])))

    missing = TARGET - countries.keys()
    if missing:
        raise SystemExit(f"no country polygon for: {', '.join(sorted(missing))}")

    provinces = {iso: [] for iso in TARGET}
    for feature in json.loads(ADMIN1.read_text())["features"]:
        iso = feature["properties"].get("adm0_a3")
        if iso not in TARGET:
            continue
        clipped = clean(clean(shape(feature["geometry"])).intersection(countries[iso]))
        if not clipped.is_empty:
            provinces[iso].append(clipped)

    state_features = []
    for iso, geoms in sorted(provinces.items()):
        if not geoms:
            continue
        national_ring = countries[iso].boundary.buffer(BORDER_EPS)
        interior = unary_union([g.boundary for g in geoms]).difference(national_ring)
        if interior.is_empty:
            continue
        state_features.append({
            "type": "Feature",
            "properties": {"country_iso_a3": iso},
            "geometry": mapping(linemerge(interior)),
        })

    country_features = [
        {
            "type": "Feature",
            "properties": {"name": NAMES[iso], "iso_a3": iso},
            "geometry": mapping(geom),
        }
        for iso, geom in sorted(countries.items())
    ]

    for feature in country_features + state_features:
        feature["geometry"]["coordinates"] = round_coords(feature["geometry"]["coordinates"])

    for name, features in (
        ("country-borders.geojson", country_features),
        ("state-borders.geojson", state_features),
    ):
        path = OUT_DIR / name
        path.write_text(
            json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":"))
        )
        print(f"{path}: {len(features)} features, {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
