# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fetches speed camera and trajectory control data from OpenStreetMap's Overpass API and outputs Mercedes-Benz COMAND Online compatible GPX (DaimlerGPXExtensions/V2.4). Tested on C-class W205 (2014).

Two tools exist:
- **`mercedespoi.py`** (primary) — Python 3 script, single command, fetches + converts
- **`convert_merc.cpp`** (legacy) — C++ tool for converting pre-existing GPX files

## Commands

```bash
# Primary: fetch and convert in one step
./mercedespoi.py --region belgium -o speedcams.gpx
./mercedespoi.py --split --region belgium -o speedcams.gpx
./mercedespoi.py --no-routes --region belgium -o speedcams.gpx
./mercedespoi.py --region antwerp -o antwerp.gpx
./mercedespoi.py --input saved.json -o offline.gpx

# Legacy C++ build (requires Qt 5.12.8+, g++, qmake)
qmake -project && qmake -makefile && make all
./mercedespoi input.gpx output.gpx
```

## Architecture

### Python Tool (`mercedespoi.py`)

Single-file, stdlib-only Python 3.6+ script (~700 lines). No external dependencies.

**Flow:**
1. Build Overpass QL query for the selected region
2. POST to Overpass API, receive JSON (not GPX/XML)
3. Parse JSON: index nodes, extract `highway=speed_camera` nodes, resolve `type=enforcement` relations (both `maxspeed` and `average_speed`)
4. Trajectory controls emit entry + exit POIs with per-POI icon/warning overrides
5. Deduplicate by coordinate (6 decimal places ≈ 11cm)
6. Write Mercedes GPX with DaimlerGPXExtensions/V2.4
7. Extract trajectory route geometry from OSM section ways, write route overlay GPX

**Key functions:**
- `build_query(region)` — Overpass QL from REGIONS dict
- `fetch_overpass(query)` — HTTP POST via `urllib.request`
- `parse_elements(data)` — 3-pass JSON parse (index nodes → speed cameras → enforcement relations), extracts maxspeed
- `normalize_maxspeed(raw)` — cleans OSM maxspeed values ("70kmh" → "70", "signals" → None)
- `_resolve_entry_exit(members, nodes)` — resolves from/to/device nodes for trajectory controls
- `haversine_m(lat1, lon1, lat2, lon2)` — distance calculation for zone lengths
- `deduplicate(pois)` — coordinate-keyed dedup
- `group_by_speed(pois)` — groups POIs into speed zone buckets for `--split` mode
- `write_mercedes_gpx(pois, path, ...)` — outputs DaimlerGPXExtensions/V2.4 XML with configurable category/icon/warning
- `parse_trajectory_routes(data)` — extracts route geometry from OSM section ways
- `chain_way_segments(segments)` — chains multiple OSM ways into continuous routes
- `write_trajectory_routes_gpx(routes, path)` — outputs route GPX with `<gpx:rte>` elements

**Regions** defined in `REGIONS` dict: `belgium` (area 3600052411), `antwerp` (Province of Antwerp).

### Legacy C++ Tool (`convert_merc.cpp`)

Single-file Qt5 C++ application (~93 lines). Line-by-line string matching parser — requires xmllint-preprocessed input with consistent line endings.

**Legacy pipeline:** curl_fetch.sh → conver_xml2pgx.sh (gpsbabel) → xmllint → mercedespoi

## Mercedes GPX Extensions (DaimlerGPXExtensions/V2.4)

Per-waypoint extensions added:
- `WptIconId` (IconId="6" = camera icon)
- `POICategory` (Cat="Speedcamera")
- `Activity` (Active="true" Level="warning" Unit="second" Value="50")
- `Presentation` (ShowOnMap="true")
- `Address` (ISO="BE" Country="Belgium" — hardcoded)

## Key Constraints

- Country/ISO codes hardcoded to Belgium
- Activity warning value (50 seconds) hardcoded
- COMAND system hard limit: reportedly 30,000 POIs per file
- Overpass API may rate-limit; script exits with message on HTTP 429

## Data Pipeline Dependencies

- **Python tool:** Python 3.6+, internet connection (or local JSON file)
- **Legacy C++ tool:** Qt 5.12.8+, g++, qmake, gpsbabel, xmllint, curl
