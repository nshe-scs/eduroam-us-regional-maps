# eduroam US regional maps

Daily-updated KML maps of eduroam service locations, one per US state and
territory, built from the public eduroam location database and published to
GitHub Pages.

**[View the maps](https://nshe-scs.github.io/eduroam-us-regional-maps/)**

Each region's map can be dropped straight into Google Maps:

```js
new google.maps.KmlLayer({
  url: "https://nshe-scs.github.io/eduroam-us-regional-maps/eduroam_nv.kml",
  map: map,
});
```

Google caches KML for hours and won't re-fetch on a schedule you control. If you
need the map to reflect a change the moment it publishes, fetch the KML yourself
and plot the points rather than using `KmlLayer`.

## How it works

A nightly GitHub Actions run downloads the eduroam US map, clips it against the
region boundaries in `regions/`, and writes one KML per region into `docs/`
alongside a leaderboard[^1] and a changelog. If nothing changed, nothing is
committed. If something did, the run produces exactly one commit.

A service location is identified by institution, location name and coordinates.
A region's map is rebuilt when a location is **added**, **removed** or **moved**.
Upstream metadata that changes without the location changing, e.g. an updated
number of wireless access points, is logged but doesn't trigger a republish,
keeping the site from churning daily for no visible reason. Set
`"regenerate_on": "any"` to reflect every upstream edit immediately.

Placemarks are sorted alphabetically and the output contains no timestamps, so
identical input always produces byte-identical files and diffs stay readable.

`eduroam_maps.py` only needs the Python 3.8+ standard library.

## Layout

```
├── eduroam_maps.py       the job
├── make_regions.py       one-time helper to generate region files
├── config.json           settings
├── regions/              one GeoJSON polygon per region
├── docs/                 published output to be served via GitHub Pages
└── state/inventory.json  the baseline that diffs are computed against
```

`state/inventory.json` is committed alongside the maps it describes, so if a run
fails partway, the baseline and the output stay in step and the next run redoes
the work. The rest of `state/` is per-run scratch and is .gitignore'd.

## Adding, changing and removing regions

Regions are configuration, not code. A region is a GeoJSON Polygon or
MultiPolygon in `regions/`; the filename stem becomes the region code
(`nv.geojson` → `eduroam_nv.kml`) and the display name comes from the `NAME`
property. Add a file to add a region, delete it to withdraw its map.

Open a pull request to change one — `validate-regions.yml` dry-runs the job and
fails if the file can't be loaded. Regions may overlap; the leaderboard total
counts each location once.

To regenerate the whole set from census boundaries:

```bash
curl -sSL -o us_states.geojson \
  https://eric.clst.org/assets/wiki/uploads/Stuff/gz_2010_us_040_00_500k.json
python3 make_regions.py us_states.geojson regions/
```

## Outputs

| File | Contents |
|:--|:--|
| `eduroam_<code>.kml` | One region's service locations |
| `index.html` | The leaderboard, as the Pages front page |
| `LEADERBOARD.md` | The same ranking in Markdown |
| `CHANGELOG.md` | Additions, removals and moves, newest first |
| `changes.jsonl` | One JSON object per changed run |

## Configuration

| Key | Default | Meaning |
|:--|:--|:--|
| `source_url` | eduroam US KML | Upstream map |
| `min_refresh_seconds` | `3600` | Skip the network if the cached copy is younger |
| `http_timeout` | `60` | Seconds |
| `regenerate_on` | `"locations"` | `"locations"` or `"any"` |
| `placemark_icon_url` | `""` | Marker icon; empty emits no styles |
| `min_placemarks` | `100` | Abort if upstream returns fewer |
| `max_delete_ratio` | `0.5` | Abort if this fraction of locations vanishes |
| `changelog_max_entries` | `365` | Entries kept in `CHANGELOG.md` |
| `changes_max_entries` | `365` | Lines kept in `changes.jsonl` |
| `leaderboard_show_last_checked` | `false` | On, the site changes daily; off, only with the data |
| `attribution.publisher_note` | — | Who operates the site; shown first in the footnotes |
| `attribution.footnotes` | 4 notes | Data source, trademark, boundaries, code license |
| `publish.*` | — | Only used when publishing over the GitHub API instead of git |

Both guards abort the run before anything is written, so a bad upstream day
can't wipe the maps. Override with `--force` when there really is a large change.

Attribution notes accept plain text plus `[label](url)` links, and appear on the
leaderboard page, in `LEADERBOARD.md` and inside every KML — a KML travels on
its own once it's embedded in someone's map. Editing them rebuilds every map.

## Running it by hand

No arguments needed. `-v` logs progress to stderr, `-f` rebuilds everything and
bypasses the guards, `-n` computes without writing. `EDUROAM_OUTPUT_DIR`,
`EDUROAM_STATE_DIR`, `EDUROAM_REGIONS_DIR` and `EDUROAM_CONFIG` relocate the
directories; the workflow uses the first two to write into `docs/`.

```bash
EDUROAM_OUTPUT_DIR=docs EDUROAM_STATE_DIR=state ./eduroam_maps.py --dry-run -v
```

Exit `0` on success including "nothing to do", `1` on failure — download failed,
a guard tripped, another run holds the lock, or no usable regions were found.

It also runs from cron on an ordinary server. Set `publish.enabled` to `true`
with a `repo` and a token in `token_file`, and it commits through the GitHub API
instead of git.

## Deploying a copy

1. Create a public repository and add these files.
2. Generate `regions/` as above.
3. Set `publish.site_url`, `publish.repo` and `attribution.publisher_note` in
   `config.json` for your org.
4. Push, then set **Settings → Actions → General → Workflow permissions** to
   **Read and write**. Org-created repos default to read-only, and the workflow
   cannot grant itself more than the repository policy allows.
5. Run **Update eduroam maps** manually once. It commits `docs/`.
6. Set **Settings → Pages** to deploy from your branch, folder `/docs`.
7. Check the maps are served as `application/vnd.google-earth.kml+xml`:
   `curl -sI <site>/eduroam_nv.kml | grep -i content-type`.

If you protect the default branch, allow `github-actions[bot]` to bypass it, and
confirm failed workflow runs actually notify someone.

## License and attribution

The code is BSD 3-Clause — see `LICENSE`. It has no dependencies and vendors no
third-party code, and a generated KML references nothing beyond the OGC KML
namespace unless you set `placemark_icon_url`.

- **eduroam location data** is published by GÉANT. These maps are merely derived
  from GÉANT's data.
- **"eduroam"** is a registered trademark of the GÉANT Association.
- **Boundary data** from US Census cartographic files is public domain.

[^1]: The term "leaderboard" in this project does not imply superiority or inferiority; let's help each other spread secure and seamless roaming access for education.
