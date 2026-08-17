#!/usr/bin/env python3
"""Regenerate data/country-borders.geojson and data/state-borders.geojson.

Why two different sources:

* National outlines come from @geo-maps/countries-land, which is derived from
  OpenStreetMap and already clipped to the OSM coastline. That matters because
  the basemap is OSM-derived too, so the borders land on the same coastline the
  map draws. Natural Earth's outlines are generalized to a ~1:10m scale and
  visibly drift away from the basemap along the coast.
* Province divisions come from Natural Earth's admin-1 set, since there is no
  equally convenient OSM-lineage province dataset. Only the edges *shared by
  two provinces* are written out, so the outer ring never appears and nothing
  is drawn twice. Interior divisions have no basemap counterpart to disagree
  with, so their coarser lineage does not show.

  Taking shared edges is what makes the two lineages coexist. Subtracting the
  national border from the province rings instead does not work: Natural Earth
  falls short of the OSM coastline by a wide margin in places (~42,000 km2 for
  Ukraine), so the province ring runs kilometers inside the national border and
  survives any subtraction buffer narrow enough to keep real divisions. An edge
  shared by two provinces is interior by definition, however far the outline
  drifts.

Where two selected countries are neighbours their shared border is drawn twice,
once per country, and the source does not always agree with itself: Lebanon's
and Israel's outlines coincide exactly for most of their shared length but
overlap over about 1 km2 near the coast. Both lines mean the same border there,
so one copy is dropped — see dedupe_shared_borders.

Usage:
    pip install shapely
    npm install @geo-maps/countries-land-100m @geo-maps/earth-lands-100m
    curl -O https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
    python3 scripts/build-borders.py

To change which countries are drawn, edit TARGET/NAMES below.
"""

import json
from itertools import combinations
from pathlib import Path

import shapely
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import linemerge, unary_union
from shapely.prepared import prep
from shapely.strtree import STRtree
from shapely.validation import make_valid

TARGET = {"UKR", "LBN", "ISR", "YEM", "IRN", "SDN", "IRQ"}
NAMES = {
    "UKR": "Ukraine",
    "LBN": "Lebanon",
    "ISR": "Israel",
    "YEM": "Yemen",
    "IRN": "Iran",
    "SDN": "Sudan",
    "IRQ": "Iraq",
}

COUNTRIES_LAND = Path("node_modules/@geo-maps/countries-land-100m/map.geo.json")
EARTH_LAND = Path("node_modules/@geo-maps/earth-lands-100m/map.geo.json")
ADMIN1 = Path("ne_10m_admin_1_states_provinces.geojson")
OUT_DIR = Path("data")

# Drop islets below ~1 km2. They are invisible at the zooms this map uses and
# make up a large share of the vertex count.
MIN_AREA = 1e-4
# ~1m of precision, which is finer than the source data resolves.
PRECISION = 5
# ~9km. Widest strip between two neighbours still read as the two of them
# disagreeing about one border. Enough to clear the Lebanon/Israel case, which
# parts by up to 5.5km; anything wider only widens what counts as disputed.
DISPUTE_WIDTH = 0.08
# ~2km. Open border fragments shorter than this are offcuts of the deduplication
# rather than border anyone would miss.
MIN_STUB = 0.02


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


def polygonal(geom):
    if geom.is_empty:
        return []
    return [g for g in getattr(geom, "geoms", [geom]) if g.geom_type in ("Polygon", "MultiPolygon")]


def dedupe_shared_borders(countries, earth_land, all_land):
    """Return one border line per country, with shared stretches drawn once.

    Two neighbours each carry the border between them in their own outline. Where
    those outlines agree the strokes land on top of each other and nobody notices,
    but where the source disagrees you get two lines several kilometers apart.

    What gets dropped is keyed on the area the two outlines disagree about:
    pockets of no-man's land between them, plus anywhere they overlap. Both sides
    of such a pocket describe the same border, so the second country's copy goes.
    Keying on that area rather than on plain proximity is what keeps this honest —
    a proximity rule wide enough to catch a 5km disagreement also erases 8km of
    Lebanese coast and 6km near the Syrian tripoint, because a coast that merely
    passes close to the neighbour is not a duplicate of anything.

    Ground that lies between the two but belongs to somebody is not a pocket, so
    two masks are applied. Anything a third country claims is subtracted: most of
    what separates Lebanon from Israel is Syria, and without this the whole
    Lebanon/Syria border reads as a gap between the pair and is deleted, leaving
    the southeast of Lebanon with no border at all. Then what is left is
    intersected with real land: closing the gap between two countries also spans
    the water where their coastlines converge at the border's seaward end, and
    that patch of sea is bounded by both countries' coasts, making it
    indistinguishable from no-man's land on geometry alone. Disputed territory is
    land, and it is claimed by neither neighbour; the two masks say so.

    Which country keeps the shared stretch is decided by ISO code order. The
    lines are identical in style, so the choice is not visible; it only needs to
    be deterministic.
    """
    lines = {iso: geom.boundary for iso, geom in countries.items()}
    for first, second in combinations(sorted(countries), 2):
        a, b = countries[first], countries[second]
        if a.distance(b) > DISPUTE_WIDTH:
            continue
        merged = unary_union([a, b])
        pockets = (
            merged.buffer(DISPUTE_WIDTH)
            .buffer(-DISPUTE_WIDTH)
            .difference(merged)
            .intersection(a.buffer(DISPUTE_WIDTH))
            .intersection(b.buffer(DISPUTE_WIDTH))
            .intersection(local_land(earth_land, merged))
            .difference(third_party_land(all_land, (first, second), merged))
        )
        disputed = unary_union(polygonal(clean(pockets)) + polygonal(a.intersection(b)))
        if disputed.is_empty:
            continue
        duplicate = lines[second].intersection(disputed.boundary.buffer(1e-7))
        if not duplicate.is_empty:
            lines[second] = drop_stubs(lines[second].difference(duplicate.buffer(1e-7)))
    return lines


def local_land(earth_land, around):
    """Land near `around`, as a rectangle clipped out of the global land mask.

    clip_by_rect is used rather than a plain intersection because the mask is one
    multipolygon covering every landmass on earth, and a rectangle clip is the
    only operation on it that finishes quickly.
    """
    return clean(shapely.clip_by_rect(earth_land, *neighbourhood(around).bounds))


def third_party_land(all_land, pair, around):
    """Territory near `around` belonging to any country outside `pair`."""
    box = prep(neighbourhood(around))
    claimed = [
        clean(shape(feature["geometry"]))
        for feature in all_land
        if feature["properties"].get("A3") not in pair
        and box.intersects(shape(feature["geometry"]))
    ]
    return clean(unary_union(claimed)) if claimed else Polygon()


def neighbourhood(around):
    return around.buffer(DISPUTE_WIDTH * 4).envelope


def drop_stubs(line):
    """Discard the short open fragments left behind when a stretch is removed.

    Closed rings are kept whatever their length: those are islands, not offcuts.
    """
    parts = [
        part
        for part in getattr(line, "geoms", [line])
        if part.is_closed or part.length > MIN_STUB
    ]
    return unary_union(parts)


def main():
    land_features = json.loads(COUNTRIES_LAND.read_text())["features"]
    countries = {}
    for feature in land_features:
        iso = feature["properties"].get("A3")
        if iso in TARGET:
            countries[iso] = fill_holes(clean(shape(feature["geometry"])))

    missing = TARGET - countries.keys()
    if missing:
        raise SystemExit(f"no country polygon for: {', '.join(sorted(missing))}")

    earth_land = shape(json.loads(EARTH_LAND.read_text())["geometries"][0])

    # Kept unclipped: shared edges are found by exact boundary intersection, so
    # the provinces have to stay topologically matched the way Natural Earth
    # ships them. Clipping happens afterwards, on the extracted lines.
    provinces = {iso: [] for iso in TARGET}
    for feature in json.loads(ADMIN1.read_text())["features"]:
        iso = feature["properties"].get("adm0_a3")
        if iso in TARGET:
            provinces[iso].append(clean(shape(feature["geometry"])))

    state_features = []
    for iso, geoms in sorted(provinces.items()):
        if len(geoms) < 2:
            continue
        tree = STRtree(geoms)
        shared = []
        for i, geom in enumerate(geoms):
            for j in tree.query(geom):
                if j <= i:  # each pair once
                    continue
                touching = geom.boundary.intersection(geoms[j].boundary)
                if touching.is_empty:
                    continue
                shared.extend(
                    part
                    for part in getattr(touching, "geoms", [touching])
                    if part.geom_type in ("LineString", "MultiLineString")
                )
        if not shared:
            continue
        interior = linemerge(unary_union(shared)).intersection(countries[iso])
        if interior.is_empty:
            continue
        state_features.append({
            "type": "Feature",
            "properties": {"country_iso_a3": iso},
            "geometry": mapping(interior),
        })

    country_features = [
        {
            "type": "Feature",
            "properties": {"name": NAMES[iso], "iso_a3": iso},
            "geometry": mapping(linemerge(line) if line.geom_type != "LineString" else line),
        }
        for iso, line in sorted(dedupe_shared_borders(countries, earth_land, land_features).items())
        if not line.is_empty
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
