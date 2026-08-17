#!/usr/bin/env python3
"""Write data/occupied-ukraine.geojson from the latest DeepState snapshot.

DeepStateUA publishes a daily assessment of Russian-occupied territory in
Ukraine; cyterat/deepstate-map-data mirrors it to GitHub as GeoJSON, one
feature per day. This takes the most recent one.

Unlike the borders, this is an *assessment*, not a survey. Other trackers —
ISW most prominently — draw the line differently, and all of them are
inferring control from open sources. Treat the date on the output as part of
the data.

Usage:
    python3 scripts/fetch-occupied.py
"""

import gzip
import json
import urllib.request
from pathlib import Path

SOURCE = (
    "https://raw.githubusercontent.com/cyterat/deepstate-map-data/main/"
    "deepstate-map-data.geojson.gz"
)
ATTRIBUTION = "DeepStateUA via github.com/cyterat/deepstate-map-data"
OUT = Path("data/occupied-ukraine.geojson")
PRECISION = 5


def round_coords(obj):
    if isinstance(obj, float):
        return round(obj, PRECISION)
    if isinstance(obj, (list, tuple)):
        return [round_coords(x) for x in obj]
    return obj


def main():
    with urllib.request.urlopen(SOURCE, timeout=120) as response:
        payload = gzip.decompress(response.read())

    features = json.loads(payload)["features"]
    # Two thirds of the archive carries a null date; only the dated ones can be
    # ranked, and the newest of those is the current assessment.
    dated = [f for f in features if f["properties"].get("date")]
    if not dated:
        raise SystemExit("no dated snapshot in the archive")
    latest = max(dated, key=lambda f: f["properties"]["date"])
    date = latest["properties"]["date"]

    feature = {
        "type": "Feature",
        "properties": {"date": date, "source": ATTRIBUTION},
        "geometry": {
            "type": latest["geometry"]["type"],
            "coordinates": round_coords(latest["geometry"]["coordinates"]),
        },
    }
    OUT.write_text(
        json.dumps({"type": "FeatureCollection", "features": [feature]}, separators=(",", ":"))
    )
    print(f"{OUT}: {date}, {OUT.stat().st_size // 1024} KB (newest of {len(dated)} dated snapshots)")


if __name__ == "__main__":
    main()
