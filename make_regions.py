#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright (c) 2026, Nevada System of Higher Education
# All rights reserved. See LICENSE for the full text.
"""
make_regions.py -- one-time helper that splits a US states GeoJSON into the
per-region boundary files eduroam_maps.py consumes.

This is a bootstrap tool, not part of the daily job: run it once to populate
regions/, or again to refresh the boundaries.

    curl -sSL -o us_states.geojson \\
        https://eric.clst.org/assets/wiki/uploads/Stuff/gz_2010_us_040_00_500k.json
    python3 make_regions.py us_states.geojson regions/

Any GeoJSON whose features carry a usable name property will work, so you can
point this at newer TIGER/Line exports too. Features that have a two-letter
postal code property (STUSPS) use it directly; otherwise the name is matched
against the table below. Anything unrecognised is written out using a slug of
its name, so nothing is silently dropped.
"""

import json
import os
import re
import sys

POSTAL = {
    "alabama": "al", "alaska": "ak", "arizona": "az", "arkansas": "ar",
    "california": "ca", "colorado": "co", "connecticut": "ct", "delaware": "de",
    "district of columbia": "dc", "florida": "fl", "georgia": "ga", "hawaii": "hi",
    "idaho": "id", "illinois": "il", "indiana": "in", "iowa": "ia", "kansas": "ks",
    "kentucky": "ky", "louisiana": "la", "maine": "me", "maryland": "md",
    "massachusetts": "ma", "michigan": "mi", "minnesota": "mn", "mississippi": "ms",
    "missouri": "mo", "montana": "mt", "nebraska": "ne", "nevada": "nv",
    "new hampshire": "nh", "new jersey": "nj", "new mexico": "nm", "new york": "ny",
    "north carolina": "nc", "north dakota": "nd", "ohio": "oh", "oklahoma": "ok",
    "oregon": "or", "pennsylvania": "pa", "rhode island": "ri",
    "south carolina": "sc", "south dakota": "sd", "tennessee": "tn", "texas": "tx",
    "utah": "ut", "vermont": "vt", "virginia": "va", "washington": "wa",
    "west virginia": "wv", "wisconsin": "wi", "wyoming": "wy",
    "puerto rico": "pr", "guam": "gu", "american samoa": "as",
    "northern mariana islands": "mp", "united states virgin islands": "vi",
    "us virgin islands": "vi", "virgin islands": "vi",
}

NAME_KEYS = ("NAME", "name", "Name", "STATE_NAME", "NAME_1")
CODE_KEYS = ("STUSPS", "STUSAB", "state_abbr", "abbrev")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "region"


def main(argv):
    if len(argv) != 3:
        print(__doc__.strip())
        return 2
    source, outdir = argv[1], argv[2]

    with open(source, encoding="utf-8") as fh:
        data = json.load(fh)
    os.makedirs(outdir, exist_ok=True)

    written = skipped = 0
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}
        if geom.get("type") not in ("Polygon", "MultiPolygon"):
            print(f"skip: {props.get('NAME', '?')} is a {geom.get('type')}, not an area")
            skipped += 1
            continue

        name = next((props[k] for k in NAME_KEYS if isinstance(props.get(k), str)), "")
        code = next((props[k] for k in CODE_KEYS if isinstance(props.get(k), str)), "")
        code = (code or POSTAL.get(name.strip().lower()) or slug(name)).lower()
        if not name:
            name = code.upper()

        out = {
            "type": "FeatureCollection",
            "name": name,
            "features": [
                {"type": "Feature", "properties": {"NAME": name}, "geometry": geom}
            ],
        }
        path = os.path.join(outdir, f"{code}.geojson")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, sort_keys=True)
        print(f"wrote {path}  ({name})")
        written += 1

    print(f"\n{written} region file(s) written, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

