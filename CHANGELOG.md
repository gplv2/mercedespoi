# Changelog

All notable changes to mercedespoi are documented here.

---

## 2026-01-30

### New Features

- **Single-command Python tool** — New `mercedespoi.py` replaces the entire multi-step pipeline (curl → gpsbabel → xmllint → C++ converter). Fetches speed camera data directly from OpenStreetMap's Overpass API and outputs Mercedes COMAND-compatible GPX. Zero external dependencies beyond Python 3.6+.

- **Split by speed limit** (`--split`) — Generate separate GPX files per speed zone (`belgium_30.gpx`, `belgium_50.gpx`, etc.), each with warning timing tuned to that zone's speed. Gives you different alert distances depending on how fast you're going.

- **Trajectory control alerts** — Average speed (section control) zones generate two POIs: a full sound + visual warning at the zone entry, and a quiet visual notification at the exit. Zone length is shown in the POI name.

- **Route overlay for trajectory zones** — Draws the measured sections of trajectory controls on the COMAND map as route lines. See upcoming enforcement zones from a distance, well before the entry alert fires. Copy `_routes.gpx` to the `Routes/` folder on the SD card.

- **Netherlands and combined BE+NL regions** — Query speed cameras for Belgium, the Netherlands, or both combined (`--region be-nl`). Uses Overpass area union for the combined query.

- **80 km/h speed zone** — Added for proper Netherlands coverage. Common Dutch highway limit (100 daytime / 80 nighttime) now gets its own split file and tuned warnings instead of falling into "other".

- **SD card directory layout** — Ready-to-copy `sd/` folder with `PersonalPOI/` and `Routes/` subdirectories. Generated GPX files are gitignored; directory structure is tracked.

- **Offline mode** (`--input`) — Save an Overpass API response as JSON and re-run without internet access for testing or tweaking.

### Documentation

- **Comprehensive DaimlerGPXExtensions reference** in README — All 19 icon IDs, Activity alert levels, POI limits (~30,000), SD card folder structure, route format, and country adaptation guide.

- **Warning behavior guide** (`WARNINGS.md`) — Alert timing deep-dive, seconds-to-meters conversion tables, zone tuning rationale, trajectory control design decisions, and observed COMAND behavior notes.

- **Coverage statistics** (`STATS.md`) — Country breakdown (Belgium vs Netherlands), trajectory zone characteristics, speed zone distributions, and data quality notes.

### Coverage (January 2026)

| | Belgium | Netherlands | Combined |
|---|---:|---:|---:|
| Speed cameras | 1,840 | 1,094 | 2,934 |
| Trajectory zones | 156 | 76 | 230 |
| Total POIs | 1,708 | 1,027 | 2,735 |
| Trajectory routes | 100 | 76 | 176 |

---

## 2022-03-21

### Improvements

- **OSM data pipeline** — Added Overpass API query scripts and documented the conversion steps from raw OSM data to Mercedes GPX format.

- **Qt5 build update** — Migrated C++ converter to Qt 5.12.8+ with updated build instructions.

---

## 2018-07-16

### Initial Release

- **C++ GPX converter** (`convert_merc.cpp`) — Qt5-based tool that converts GPX files to Mercedes COMAND Online format with DaimlerGPXExtensions/V2.4. Line-by-line parser for xmllint-preprocessed input.

- **Build system** — qmake/make based build. Requires Qt 5, g++, gpsbabel, xmllint, and curl.
