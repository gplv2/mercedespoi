# mercedespoi

Convert OpenStreetMap speed camera data to Mercedes-Benz COMAND Online GPX format (DaimlerGPXExtensions/V2.4).

Tested on C-class W205 (2014) with COMAND Online. Should work on any Mercedes with COMAND Online NTG 4.5 or NTG 5 (W205, W222, W213, W253, etc.).

---

## Quick Start

Requires Python 3.6+. No additional dependencies (stdlib only).

```bash
# Download all Belgian speed cameras and trajectory controls
./mercedespoi.py --region belgium -o speedcams.gpx

# Split by speed limit — one file per zone, each with tailored warnings
./mercedespoi.py --split --region belgium -o speedcams.gpx

# Test with Antwerp province only (smaller/faster)
./mercedespoi.py --region antwerp -o antwerp.gpx

# Skip route overlay generation (POIs only)
./mercedespoi.py --no-routes --region belgium -o speedcams.gpx

# Offline mode: use a previously saved Overpass JSON response
./mercedespoi.py --input saved_response.json -o offline.gpx
```

Then copy files to the SD card (see [SD Card Setup](#sd-card-setup)):
- POI files (`speedcams*.gpx`) go in the `PersonalPOI/` folder
- Route overlay file (`speedcams_routes.gpx`) goes in the `Routes/` folder

The route file is generated automatically when trajectory zones exist. It draws the measured sections on the COMAND map so you can see upcoming trajectory controls from a distance. The entry/exit POI alerts still fire independently.

---

## What It Does

1. Queries the [Overpass API](https://overpass-api.de/) for `highway=speed_camera` nodes **and** `type=enforcement` relations (both `maxspeed` and `average_speed` / trajectory controls)
2. Resolves enforcement relation member nodes to actual coordinates
3. Deduplicates cameras that share the same physical location (same camera tagged for both speed and red light, for example)
4. Outputs Mercedes COMAND-compatible GPX with DaimlerGPXExtensions
5. Generates route overlay GPX for trajectory zones — draws the measured section on the COMAND map using `<gpx:rte>` elements with road geometry from OSM way data

Example output:
```
Fetching data from Overpass API...
Speed cameras:       1840
Trajectory controls: 151
Duplicates removed:  411
Total POIs:          1580
Written to: speedcams.gpx
```

## Regions

Currently supported (extensible in the `REGIONS` dict in the script):

| Region | Description | Typical POI count |
|--------|------------|-------------------|
| `belgium` | All of Belgium (default) | ~1,580 |
| `antwerp` | Province of Antwerp only | ~285 |

Adding a new region is one line in the `REGIONS` dict — just provide an Overpass area selector.

---

## SD Card Setup

The COMAND system reads POI files from a specific folder structure on the SD card:

```
SD Card Root/
├── PersonalPOI/
│   ├── speedcams.gpx           (single file mode)
│   ├── speedcams_30.gpx        (--split: per speed zone)
│   ├── speedcams_50.gpx
│   ├── speedcams_70.gpx
│   ├── speedcams_trajectory.gpx
│   └── ...
└── Routes/
    └── speedcams_routes.gpx    (trajectory zone map overlay)
```

**Important notes:**
- The folder **must** be named `PersonalPOI` (case matters on some systems)
- The route overlay file goes in `Routes/`, not `PersonalPOI/`
- Multiple `.gpx` files are supported in each folder
- The SD card must remain inserted — POIs are read live from the card, not imported to the internal drive
- Test the SD card first by putting an MP3 file on it and playing it through COMAND, to confirm the card is readable

---

## Splitting by Speed Limit (`--split`)

Use `--split` to generate separate GPX files per speed limit zone:

```bash
./mercedespoi.py --split --region belgium -o speedcams.gpx
```

This produces:

```
speedcams_30.gpx                  52 POIs  (icon=6, warn=12s)
speedcams_50.gpx                 467 POIs  (icon=6, warn=36s)
speedcams_70.gpx                 293 POIs  (icon=6, warn=25s)
speedcams_90.gpx                  94 POIs  (icon=16, warn=20s)
speedcams_100.gpx                  5 POIs  (icon=16, warn=18s)
speedcams_120.gpx                 53 POIs  (icon=16, warn=18s)
speedcams_other.gpx              616 POIs  (icon=6, warn=36s)
                                 -----
Total                           1580 POIs
```

The output file name from `-o` is used as a base — `speedcams.gpx` produces `speedcams_30.gpx`, `speedcams_50.gpx`, etc. in the same directory.

Copy all the `speedcams_*.gpx` files to `PersonalPOI/` on the SD card:

```
PersonalPOI/
├── speedcams_30.gpx    → cameras in 30 km/h zones
├── speedcams_50.gpx    → cameras in 50 km/h zones
├── speedcams_70.gpx    → cameras in 70 km/h zones
├── speedcams_90.gpx    → cameras in 90 km/h zones
├── speedcams_100.gpx   → cameras in 100 km/h zones
├── speedcams_120.gpx   → cameras in 120 km/h zones
└── speedcams_other.gpx → cameras with unknown speed limit
```

### What each file gets

Each zone has tailored settings:

| Zone | POICategory | IconId | Warning | Effective distance at zone speed |
|------|------------|--------|---------|--------------------------------|
| 30 km/h | `Speedcam 30` | 6 (mobile cam) | 12 seconds | ~100 m at 30 km/h |
| 50 km/h | `Speedcam 50` | 6 (mobile cam) | 36 seconds | ~500 m at 50 km/h |
| 70 km/h | `Speedcam 70` | 6 (mobile cam) | 25 seconds | ~486 m at 70 km/h |
| 90 km/h | `Speedcam 90` | 16 (fixed cam) | 20 seconds | ~500 m at 90 km/h |
| 100 km/h | `Speedcam 100` | 16 (fixed cam) | 18 seconds | ~500 m at 100 km/h |
| 120 km/h | `Speedcam 120` | 16 (fixed cam) | 18 seconds | ~600 m at 120 km/h |
| Unknown | `Speedcam` | 6 (mobile cam) | 36 seconds | ~500 m at 50 km/h |

**Why time-based warnings?** `Unit="second"` is speed-adaptive. The alert fires N seconds before you reach the camera at your current speed. If you're going 50 in a 30 zone, the "12 seconds" warning still triggers at ~167m — enough to react. Fixed-distance warnings can't adapt like this.

**Why different icons?** Urban zones (30-70) use IconId 6 (camera on tripod / mobile camera). Highway zones (90+) use IconId 16 (fixed camera). This gives visual distinction on the map. You can change these in the `SPEED_ZONES` dict.

### Benefits of splitting

- **Toggle per zone** — COMAND groups POIs by `POICategory`, so you can show/hide specific speed zones
- **Tailored warnings** — short alert for urban 30 zones (where cameras are close together), longer alert on highways (where you're approaching faster)
- **Visual distinction** — different icons for urban vs. highway cameras

### Maxspeed data from OSM

The `maxspeed` tag comes directly from OpenStreetMap. Not all cameras have it — the `speedcams_other.gpx` file catches those with unknown or unusual speed limits (like `"signals"`, `"variable"`, or simply untagged). For Belgium, roughly 60% of cameras have a usable maxspeed tag.

---

# Mercedes-Benz COMAND Online GPX Format Reference

> **Standalone format reference:** See **[DAIMLER_GPX_FORMAT.md](DAIMLER_GPX_FORMAT.md)** for the comprehensive community-maintained reference covering the complete DaimlerGPXExtensions format, XSD schema history, observed behavior quirks, and all community sources. The section below is a summary.

**This section documents the DaimlerGPXExtensions format used by Mercedes-Benz COMAND Online (NTG 4.5 / NTG 5) for personal POI files.** This information has been pieced together by the community through reverse-engineering — Mercedes/Daimler has never published official public documentation. The original XSD schema files (`Daimler_GPX_Extension_V2_7_4.xsd` etc.) were hosted on daimler.com but are no longer accessible.

## Known Format Versions

| Version | Namespace URI | Found on |
|---------|--------------|----------|
| V2.4 | `http://www.daimler.com/DaimlerGPXExtensions/V2.4` | W205 C-Class (2014) |
| V2.7.2 | `http://www.daimler.com/DaimlerGPXExtensions/V2.7.2` | NTG 4.5 systems |
| V2.7.4 | `http://www.daimler.com/DaimlerGPXExtensions/V2.7.4` | W222 S-Class (NTG 5*2) |

All versions share the same element structure. COMAND appears to accept any of these version URIs interchangeably — the version number does not seem to affect compatibility.

## Complete GPX File Structure

```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<gpx:gpx creator="" version="1.1"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:gpx="http://www.topografix.com/GPX/1/1"
  xsi:schemaLocation="http://www.topografix.com/GPX/1/1
    http://www.topografix.com/GPX/1/1/gpx.xsd"
  xmlns:gpxd="http://www.daimler.com/DaimlerGPXExtensions/V2.4">

  <gpx:wpt lat="51.2123392" lon="4.4467512">
    <gpx:name>"Camera Name"</gpx:name>
    <gpx:extensions>
      <gpxd:WptExtension>
        <gpxd:WptIconId IconId="6"></gpxd:WptIconId>
        <gpxd:POICategory Cat="Speedcamera"></gpxd:POICategory>
        <gpxd:Activity Active="true" Level="warning"
          Unit="second" Value="50"></gpxd:Activity>
        <gpxd:Presentation ShowOnMap="true"></gpxd:Presentation>
        <gpxd:Address ISO="BE" Country="Belgium" State=""
          City="" CityCenter="" Street="" Street2=""
          HouseNo="" ZIP=""/>
        <gpxd:Phone Default="+32123456789"></gpxd:Phone>
      </gpxd:WptExtension>
    </gpx:extensions>
  </gpx:wpt>

  <!-- more <gpx:wpt> elements ... -->

</gpx:gpx>
```

**Note:** The `gpx:` prefix on standard GPX elements (`gpx:gpx`, `gpx:wpt`, `gpx:name`, `gpx:extensions`) is required. The `gpxd:` prefix is used for all Daimler extension elements.

## Extension Elements Reference

There are **6 known elements** inside `<gpxd:WptExtension>`. All are optional.

### 1. WptIconId — Map Icon

```xml
<gpxd:WptIconId IconId="6"></gpxd:WptIconId>
```

Sets the icon displayed on the map for this POI. See the [full icon table](#poi-icon-ids-1-19) below.

### 2. POICategory — Category Name

```xml
<gpxd:POICategory Cat="Speedcamera"></gpxd:POICategory>
```

A free-text string. This is the category name shown in COMAND when browsing POIs. You can use any string. POIs with the same `Cat` value are grouped together, which is useful for toggling visibility per category.

Practical examples:
- `Cat="Speedcamera"`
- `Cat="Speedcam 30"` / `Cat="Speedcam 50"` / `Cat="Speedcam 120"` (split by zone)
- `Cat="Trajectory"` (for average speed checks)
- `Cat="Restaurants"`, `Cat="Hotels"`, etc.

### 3. Activity — Warning Behavior

> **Deep dive:** See [WARNINGS.md](WARNINGS.md) for the full technical reference — conversion tables, speed-adaptive math, zone tuning rationale, dual-warning workarounds, and common configurations.

```xml
<gpxd:Activity Active="true" Level="warning" Unit="second" Value="50"></gpxd:Activity>
```

Controls if and how COMAND alerts you when approaching this POI.

| Attribute | Values | Description |
|-----------|--------|-------------|
| `Active` | `"true"` / `"false"` | Enable/disable the alert |
| `Level` | `"warning"` | **Visual + audio** alert (most noticeable) |
| | `"information"` | **Visual only** — icon highlight on map, no sound |
| | `"sound"` | **Audio only** — beep/tone, no visual popup |
| `Unit` | `"second"` | Time before reaching the POI (**speed-adaptive** — see below) |
| | `"kilometer"` | Fixed distance in km |
| | `"mile"` | Fixed distance in miles |
| `Value` | numeric | The distance/time value. **Supports decimals** (e.g., `"0.5"`, `"0.1"`) |

#### Understanding Time vs. Distance Triggers

**`Unit="second"` is speed-adaptive** and often the best choice. The alert fires N seconds before you reach the POI at your current speed. This means:

| Value (seconds) | At 30 km/h | At 50 km/h | At 70 km/h | At 90 km/h | At 120 km/h |
|-----------------|-----------|-----------|-----------|-----------|------------|
| `"9"` (common default) | 75 m | 125 m | 175 m | 225 m | 300 m |
| `"18"` | 150 m | 250 m | 350 m | 450 m | 600 m |
| `"36"` | 300 m | 500 m | 700 m | 900 m | 1200 m |
| `"50"` | 417 m | 694 m | 972 m | 1250 m | 1667 m |

**`Unit="kilometer"` is fixed-distance** — the alert always fires at the same distance regardless of speed:

| Value (km) | Distance |
|------------|----------|
| `"0.1"` | 100 meters |
| `"0.5"` | 500 meters |
| `"1"` | 1 kilometer |

#### Can You Get Two Warnings? (500m Sound + 100m Visual)

**Not directly with a single POI.** Each waypoint supports only one `Activity` element, which means one trigger at one distance with one alert type.

Possible workarounds (untested):

1. **Two files with duplicate entries** — one file with `Level="sound" Unit="kilometer" Value="0.5"` (audio beep at 500m) and another with `Level="warning" Unit="kilometer" Value="0.1"` (full alert at 100m). Each file has the same POIs. Whether COMAND fires both alerts for duplicate coordinates is unconfirmed — it may deduplicate.

2. **Use time-based warnings as a compromise** — `Unit="second" Value="36"` gives ~500m warning at 50 km/h and ~1200m at highway speed. This gives one alert that adapts to your speed. At 50km/h this puts the warning at almost exactly 500m.

3. **Split by speed zone for tailored warnings** — use separate files with different Activity settings per speed limit (see [Splitting by Speed Limit](#future-splitting-by-speed-limit)):
   - `speedcams_30.gpx`: `Value="12" Unit="second"` (~100m at 30 km/h)
   - `speedcams_50.gpx`: `Value="36" Unit="second"` (~500m at 50 km/h)
   - `speedcams_120.gpx`: `Value="18" Unit="second"` (~600m at 120 km/h)

**Recommended practical setting:** `Level="warning" Unit="second" Value="36"` — this gives a combined audio+visual alert roughly 500m before the camera at urban speeds, scaling up proportionally at highway speeds. It's a single alert but it's the most effective compromise.

### 4. Presentation — Map Visibility

```xml
<gpxd:Presentation ShowOnMap="true"></gpxd:Presentation>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `ShowOnMap` | `"true"` / `"false"` | Whether the POI icon appears on the navigation map |

Set to `"false"` if you want the alert to fire when approaching but don't want to clutter the map with icons.

### 5. Address — Location Details

```xml
<gpxd:Address ISO="BE" Country="Belgium" State="" City="Brussels"
  CityCenter="" Street="Rue de la Loi" Street2="" HouseNo="16" ZIP="1000"/>
```

| Attribute | Description |
|-----------|-------------|
| `ISO` | ISO 3166-1 alpha-2 country code (`"BE"`, `"DE"`, `"FR"`, `"NL"`, etc.) |
| `Country` | Country name |
| `State` | State/province/region |
| `City` | City name |
| `CityCenter` | City center designation |
| `Street` | Street name |
| `Street2` | Additional street info |
| `HouseNo` | House number |
| `ZIP` | Postal code |

All attributes are optional strings. Empty values (`""`) are acceptable. The address is shown when you select the POI in COMAND.

### 6. Phone — Telephone Number

```xml
<gpxd:Phone Default="+32 2 123 45 67"></gpxd:Phone>
```

| Attribute | Description |
|-----------|-------------|
| `Default` | Phone number string (free-text) |

When set, the phone number appears in the POI details and can be dialed directly through COMAND's phone integration (if a phone is paired via Bluetooth). Useful for POIs like restaurants or hotels. Not relevant for speed cameras.

## POI Icon IDs (1-19)

The COMAND system has **19 built-in icons** for personal POIs. You cannot add custom icons. Most are red. Any IconId value of 20 or higher defaults to the same icon as 19.

| IconId | Icon | Suggested Use |
|--------|------|---------------|
| 1 | Crosshairs / target with "@" | General POI |
| 2 | Fishing hook | Fishing spots |
| 3 | Beach sunbed | Beaches, pools |
| 4 | Tent | Camping sites |
| 5 | Campfire | Campsites, BBQ areas |
| **6** | **Camera on tripod** (mobile camera) | **Speed cameras (default)** |
| 7 | Heart | Favorites, personal places |
| 8 | Log cabin | Cabins, lodges |
| 9 | Picnic blanket | Picnic areas, parks |
| 10 | Skis | Ski resorts, winter sports |
| 11 | Fork, knife, plate with heart | Favorite restaurants |
| 12 | Map pin | General marked locations |
| 13 | Car | Parking, garages, car services |
| 14 | Bed | Hotels, accommodation |
| 15 | Shopping bag | Shopping, stores |
| **16** | **Camera (fixed)** | **Fixed speed cameras** |
| 17 | Running man | Sports, jogging routes |
| 18 | Green petrol pump | Gas stations |
| 19 | Crosshairs / target | General POI |

**For speed cameras specifically:**
- `IconId="6"` (camera on tripod) is the most commonly used — it's the default for most community POI files
- `IconId="16"` (fixed camera) could be used to distinguish fixed installations
- `IconId="7"` (heart) is noted as being more visible on the map than the camera icons, as a workaround

Community note: because everyone defaults to `IconId="6"`, all personal POIs (WiFi hotspots, cameras, restaurants) end up looking the same. Using the split-by-category approach with different icons per file helps distinguish them.

## POI Limits

| Limit | Details |
|-------|---------|
| **Maximum POIs** | **~25,000 - 30,000** total across all files on the SD card |
| **Failure mode** | If exceeded, **ALL POIs on the entire SD card are ignored** — not just the excess |
| **Per file** | No known per-file limit (within the total limit) |
| **Multiple files** | Fully supported — COMAND reads all `.gpx` files in the `PersonalPOI` folder |

Belgium has ~1,580 speed cameras, so even with duplication across split files you're well within limits. All of Europe might push closer to the limit.

## Trajectory Route Overlay

The tool automatically generates a route overlay file for trajectory (average speed) zones. This draws the measured sections on the COMAND map as route lines, giving you visual awareness of upcoming trajectory controls well before the entry alert fires.

**How it works:**

- Each trajectory enforcement relation in OSM contains `section` way members — the actual road geometry of the measured section
- The tool chains these ways into continuous routes and writes them as `<gpx:rte>` elements
- Output file: `{basename}_routes.gpx` (e.g., `speedcams_routes.gpx`)
- Copy to `Routes/` folder on the SD card (separate from POIs in `PersonalPOI/`)

**Belgium stats:** ~100 trajectory routes, ~3,400 waypoints tracing the road geometry.

**Route + POI alerts work together:**

| Layer | What | Where on SD card |
|---|---|---|
| POI alerts | Sound + visual at zone entry, visual at zone exit | `PersonalPOI/` |
| Route overlay | Visible line on map showing the measured section | `Routes/` |

The route overlay does **not** trigger alerts — routes don't support the `Activity` element. That's why you need both: POIs for alerts, routes for map visualization.

To disable route generation:
```bash
./mercedespoi.py --no-routes --region belgium -o speedcams.gpx
```

**Route GPX format reference:**

```xml
<gpx:rte>
  <gpx:name>Trajectory 70: Trajectcontrole N126</gpx:name>
  <gpx:extensions>
    <gpxd:RteExtension>
      <gpxd:RouteLength Unit="kilometer" Value="2.10"/>
    </gpxd:RteExtension>
  </gpx:extensions>
  <gpx:rtept lat="51.1483" lon="4.9963"/>
  <gpx:rtept lat="51.1482" lon="4.9966"/>
  <!-- ... ordered points tracing the road -->
</gpx:rte>
```

---

## OpenStreetMap Data Sources

The script queries both legacy nodes and modern enforcement relations:

### Legacy: `highway=speed_camera` Nodes

The original and still most common way speed cameras are mapped in OSM. A simple node with `highway=speed_camera` tag, often with `maxspeed=*` indicating the enforced speed limit.

### Modern: Enforcement Relations

The recommended OSM tagging approach uses `type=enforcement` relations:
- `enforcement=maxspeed` — point speed cameras
- `enforcement=average_speed` — trajectory/section control cameras (multiple cameras measuring average speed over a distance)

Enforcement relations have member nodes with roles:
- `device` — the physical camera device (preferred for coordinates)
- `from` — start of enforcement section (fallback for coordinates)
- `to` — end of enforcement section (for trajectory controls)

### Deduplication

Many Belgian cameras are tagged both as a `highway=speed_camera` node AND as part of an `enforcement` relation. The script deduplicates by rounding coordinates to 6 decimal places (~11 cm precision) — if two POIs share the same physical location, only the first is kept.

---

## Legacy: Manual Pipeline (C++ Tool)

The original C++ tool (`convert_merc.cpp`) converts pre-existing GPX files exported from Overpass Turbo. It still works if you have GPX files from other sources:

```bash
# 1. Fetch from Overpass API
bash curl_fetch.sh

# 2. Convert OSM XML to GPX via gpsbabel
bash conver_xml2pgx.sh

# 3. Normalize line endings (required — the C++ parser depends on this)
xmllint --format --pretty 1 speed.gpx > pretty_speed.gpx

# 4. Build the C++ converter (requires Qt 5.12.8+, g++, qmake)
qmake -project && qmake -makefile && make all

# 5. Convert to Mercedes format
./mercedespoi pretty_speed.gpx output.gpx
```

The Python script replaces this entire pipeline with a single command.

---

## Country Note

Country/ISO codes and the Overpass area selector are currently set to Belgium. To adapt for other countries:

1. Add a new entry to the `REGIONS` dict with the appropriate Overpass area selector (use `area(36000XXXXX)` where XXXXX is the OSM relation ID of the country)
2. Modify the `Address` element's `ISO` and `Country` attributes in `write_mercedes_gpx()`

Examples of OSM relation IDs for area selectors:
- Belgium: `area(3600052411)` (relation 52411)
- Netherlands: `area(3600047796)` (relation 47796)
- Germany: `area(3600051477)` (relation 51477)
- France: `area(3600001403)` (relation 1403)
- Luxembourg: `area(3600002171)` (relation 2171)

Formula: Overpass area ID = 3600000000 + OSM relation ID.

---

## Contributing & Sources

The DaimlerGPXExtensions format has never been officially documented by Mercedes-Benz. Everything in this document is community knowledge built from reverse-engineering, trial-and-error, and forum discussions. If you discover something new, please contribute!

### Key community resources

- [blog.papalima.com — Adding POIs to Mercedes-Benz COMAND / NAVI](http://blog.papalima.com/2017/04/adding-pois-to-mercedes-benz-comand-navi.html) — icon screenshots, SD card setup, practical guide
- [mercedes-forum.com — Import persoenlicher Sonderziele ins COMAND Online NTG 4.5](https://www.mercedes-forum.com/threads/import-persoenlicher-sonderziele-poi-und-routen-ins-comand-online-ntg-4-5.81278/) — most complete format documentation, includes route format
- [MHH AUTO — COMAND POI Daimler GPX extensions](https://mhhauto.com/Thread-COMAND-POI-Daimler-gpx-extensions) — community efforts to reconstruct the XSD schema
- [MBClub UK — NAVI personal POI icons for COMAND](https://forums.mbclub.co.uk/threads/navi-personal-poi-icons-for-c0mand.222691/) — icon testing and identification
- [MBWorld — SatNav / NAVI POI format](https://mbworld.org/forums/s-class-w222/664089-satnav-navi-poi-format.html) — V2.7.4 format for W222
- [Kurviger Forum — Importing GPX with Daimler XSD extensions](https://forum.kurviger.com/t/importing-gpx-file-containing-daimler-xsd-extensions-fails-as-xsd-is-missing/12819) — notes on the broken XSD URLs

### Data sources

- [OpenStreetMap](https://www.openstreetmap.org/) via [Overpass API](https://overpass-api.de/) — speed camera data, ODbL licensed
- [scdb.info](https://www.scdb.info/) — European speed camera database (alternative source)
- [poi.gps-data-team.com](https://poi.gps-data-team.com/) — community POI files for various GPS systems

---

## License

The speed camera data comes from OpenStreetMap and is licensed under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).
