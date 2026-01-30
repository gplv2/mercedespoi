# DaimlerGPXExtensions Format Reference

**A community-maintained reference for the Mercedes-Benz COMAND Online personal POI and route GPX format.**

Mercedes-Benz / Daimler AG has never published public documentation for this format. The original XSD schema files (`Daimler_GPX_Extension_V2_4.xsd`, `V2_7_2`, `V2_7_4`) were once hosted on `daimler.com` but are no longer accessible. Everything in this document has been reconstructed through community reverse-engineering, trial-and-error, forum discussions, and hands-on testing.

**Applies to:** Mercedes-Benz COMAND Online NTG 4.5 and NTG 5 (W205 C-Class, W222 S-Class, W213 E-Class, W253 GLC, and similar models from ~2014 onwards).

---

## Table of Contents

- [Format Versions](#format-versions)
- [File Structure](#file-structure)
- [Extension Elements](#extension-elements)
  - [1. WptIconId — Map Icon](#1-wpticonid--map-icon)
  - [2. POICategory — Category Name](#2-poicategory--category-name)
  - [3. Activity — Warning Behavior](#3-activity--warning-behavior)
  - [4. Presentation — Map Visibility](#4-presentation--map-visibility)
  - [5. Address — Location Details](#5-address--location-details)
  - [6. Phone — Telephone Number](#6-phone--telephone-number)
- [POI Icon Table (1-19)](#poi-icon-table-119)
- [Activity Deep Dive](#activity-deep-dive)
  - [Alert Levels](#alert-levels)
  - [Trigger Units](#trigger-units)
  - [Seconds-to-Meters Conversion Table](#seconds-to-meters-conversion-table)
  - [Time vs Distance — When to Use Which](#time-vs-distance--when-to-use-which)
  - [Dual Warning Workarounds](#dual-warning-workarounds)
  - [Common Configurations](#common-configurations)
- [Route Format](#route-format)
- [SD Card Structure](#sd-card-structure)
- [POI Limits](#poi-limits)
- [Observed Behavior and Quirks](#observed-behavior-and-quirks)
- [XSD Schema History](#xsd-schema-history)
- [Community Sources](#community-sources)

---

## Format Versions

| Version | Namespace URI | Known Systems |
|---------|--------------|---------------|
| V2.4 | `http://www.daimler.com/DaimlerGPXExtensions/V2.4` | W205 C-Class (2014), NTG 4.5 |
| V2.7.2 | `http://www.daimler.com/DaimlerGPXExtensions/V2.7.2` | NTG 4.5 systems |
| V2.7.4 | `http://www.daimler.com/DaimlerGPXExtensions/V2.7.4` | W222 S-Class, NTG 5*2 |

All versions share the same element structure. COMAND appears to accept any of these version URIs interchangeably — the version number does not seem to affect compatibility. If unsure, use V2.4.

---

## File Structure

A complete DaimlerGPXExtensions POI file:

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
        <gpxd:Phone Default="+32 2 123 45 67"></gpxd:Phone>
      </gpxd:WptExtension>
    </gpx:extensions>
  </gpx:wpt>

  <!-- more <gpx:wpt> elements ... -->

</gpx:gpx>
```

**Important syntax notes:**

- The `gpx:` prefix on standard GPX elements (`gpx:gpx`, `gpx:wpt`, `gpx:name`, `gpx:extensions`) is **required**
- The `gpxd:` prefix is used for all Daimler extension elements
- The `creator=""` attribute can be empty
- File encoding must be UTF-8
- File extension must be `.gpx`

---

## Extension Elements

There are **6 known elements** inside `<gpxd:WptExtension>`. All are optional — a waypoint with no extensions will display as a generic POI on the map.

### 1. WptIconId — Map Icon

```xml
<gpxd:WptIconId IconId="6"></gpxd:WptIconId>
```

Sets the icon displayed on the COMAND map for this POI. COMAND has 19 built-in icons numbered 1-19. See the [full icon table](#poi-icon-table-119) below. Custom icons are not supported.

If omitted or set to an invalid value, COMAND uses a default icon.

### 2. POICategory — Category Name

```xml
<gpxd:POICategory Cat="Speedcamera"></gpxd:POICategory>
```

A **free-text string**. This is the category name shown in COMAND when browsing POIs by category. You can use any string you like.

POIs with the same `Cat` value are **grouped together** in the category browser, which allows toggling visibility per category. This is useful for organizing different types of POIs:

- `Cat="Speedcamera"` — all cameras in one group
- `Cat="Speedcam 30"` / `Cat="Speedcam 50"` / `Cat="Speedcam 120"` — split by zone
- `Cat="Restaurants"` / `Cat="Hotels"` / `Cat="Parking"` — general POI use

### 3. Activity — Warning Behavior

```xml
<gpxd:Activity Active="true" Level="warning" Unit="second" Value="36"></gpxd:Activity>
```

Controls if and how COMAND alerts you when approaching this POI. This is the most powerful and complex element. See the [Activity Deep Dive](#activity-deep-dive) section for full details.

| Attribute | Required | Values | Description |
|-----------|----------|--------|-------------|
| `Active` | Yes | `"true"` / `"false"` | Enable or disable the alert |
| `Level` | Yes | `"warning"` / `"information"` / `"sound"` | Type of alert (see below) |
| `Unit` | Yes | `"second"` / `"kilometer"` / `"mile"` | How the trigger distance is measured |
| `Value` | Yes | Numeric string | The distance or time value. Supports decimals (e.g., `"0.5"`) |

### 4. Presentation — Map Visibility

```xml
<gpxd:Presentation ShowOnMap="true"></gpxd:Presentation>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `ShowOnMap` | `"true"` / `"false"` | Whether the POI icon appears on the navigation map |

Set to `"false"` if you want the Activity alert to fire when approaching but don't want the POI icon cluttering the map. The alert will still trigger — this only controls the icon visibility.

### 5. Address — Location Details

```xml
<gpxd:Address ISO="BE" Country="Belgium" State="Antwerp"
  City="Mechelen" CityCenter="" Street="Brusselsesteenweg"
  Street2="" HouseNo="42" ZIP="2800"/>
```

| Attribute | Description |
|-----------|-------------|
| `ISO` | ISO 3166-1 alpha-2 country code (`"BE"`, `"NL"`, `"DE"`, `"FR"`, etc.) |
| `Country` | Country name (free text) |
| `State` | State, province, or region |
| `City` | City name |
| `CityCenter` | City center designation |
| `Street` | Street name |
| `Street2` | Additional street information |
| `HouseNo` | House number |
| `ZIP` | Postal/ZIP code |

All attributes are **optional** strings. Empty values (`""`) are acceptable and commonly used for fields that don't apply. The address is shown when you select the POI in COMAND's POI details screen.

### 6. Phone — Telephone Number

```xml
<gpxd:Phone Default="+32 2 123 45 67"></gpxd:Phone>
```

| Attribute | Description |
|-----------|-------------|
| `Default` | Phone number (free-text string) |

When set, the phone number appears in the POI details screen and can be **dialed directly** through COMAND's phone integration (if a phone is paired via Bluetooth). Useful for restaurants, hotels, or businesses — not relevant for speed cameras.

---

## POI Icon Table (1-19)

The COMAND system has **19 built-in icons** for personal POIs. You **cannot** add custom icons. Most icons are red. Any `IconId` value of 20 or higher falls back to the default icon.

| IconId | Icon Description | Suggested Use |
|--------|-----------------|---------------|
| 1 | Crosshairs / target with "@" | General POI, email-related |
| 2 | Fishing hook | Fishing spots |
| 3 | Beach sunbed / flag | Beaches, pools, "finish line" markers |
| 4 | Tent | Camping sites |
| 5 | Campfire | Campsites, BBQ areas |
| **6** | **Camera on tripod** | **Speed cameras (community default)** |
| 7 | Heart | Favorites, personal places |
| 8 | Log cabin | Cabins, mountain lodges |
| 9 | Picnic blanket | Picnic areas, parks |
| 10 | Skis | Ski resorts, winter sports |
| 11 | Fork, knife, plate with heart | Favorite restaurants |
| 12 | Map pin | General marked locations |
| 13 | Car | Parking, garages, car services |
| 14 | Bed | Hotels, accommodation |
| 15 | Shopping bag | Shopping centers, stores |
| **16** | **Camera (fixed)** | **Fixed speed cameras, CCTV** |
| 17 | Running man | Sports locations, jogging routes |
| 18 | Green petrol pump | Gas stations |
| 19 | Crosshairs / target | General POI |

**Practical notes:**
- `IconId="6"` (camera on tripod) is the community default for speed cameras. Almost every community POI file uses it.
- `IconId="16"` (fixed camera) can be used to distinguish fixed installations from mobile camera locations.
- `IconId="7"` (heart) has been reported as being more visible on the map than the camera icons — a workaround if you find camera icons too small.
- Because everyone uses `IconId="6"`, all personal POIs (WiFi hotspots, cameras, restaurants) end up looking the same. Using different icons per category helps distinguish them.

---

## Activity Deep Dive

The `Activity` element is the most powerful feature of DaimlerGPXExtensions. It turns static map pins into active alerts that notify you when you're approaching a POI.

### Alert Levels

| Level | Visual | Audio | Behavior |
|-------|--------|-------|----------|
| `"warning"` | Popup on screen | Alert tone | Most noticeable — use for things you must react to |
| `"information"` | Icon highlight / notification | None | Visual-only — use for interesting but non-urgent locations |
| `"sound"` | None | Brief tone | Audio-only — subtle advance notice |

### Trigger Units

#### `Unit="second"` — Speed-Adaptive (Recommended)

The alert fires **N seconds before you reach the POI** at your current speed. The trigger distance scales automatically:

- Driving fast → alert fires farther away → more distance to react
- Driving slowly → alert fires closer → less unnecessary noise
- Stationary (speed = 0) → alert does not fire

**Formula:** `distance_meters = speed_kmh × value_seconds / 3.6`

#### `Unit="kilometer"` — Fixed Distance

The alert fires at a **fixed distance** regardless of speed. Decimal values are supported (`"0.5"` = 500 meters).

#### `Unit="mile"` — Fixed Distance (Imperial)

Same as kilometer but in miles. For UK/US use.

### Seconds-to-Meters Conversion Table

| Value (s) | 30 km/h | 50 km/h | 70 km/h | 80 km/h | 90 km/h | 100 km/h | 120 km/h | 130 km/h |
|-----------|---------|---------|---------|---------|---------|----------|----------|----------|
| **5** | 42 m | 69 m | 97 m | 111 m | 125 m | 139 m | 167 m | 181 m |
| **9** | 75 m | 125 m | 175 m | 200 m | 225 m | 250 m | 300 m | 325 m |
| **12** | 100 m | 167 m | 233 m | 267 m | 300 m | 333 m | 400 m | 433 m |
| **18** | 150 m | 250 m | 350 m | 400 m | 450 m | 500 m | 600 m | 650 m |
| **20** | 167 m | 278 m | 389 m | 444 m | 500 m | 556 m | 667 m | 722 m |
| **22** | 183 m | 306 m | 428 m | 489 m | 550 m | 611 m | 733 m | 794 m |
| **25** | 208 m | 347 m | 486 m | 556 m | 625 m | 694 m | 833 m | 903 m |
| **30** | 250 m | 417 m | 583 m | 667 m | 750 m | 833 m | 1000 m | 1083 m |
| **36** | 300 m | 500 m | 700 m | 800 m | 900 m | 1000 m | 1200 m | 1300 m |
| **50** | 417 m | 694 m | 972 m | 1111 m | 1250 m | 1389 m | 1667 m | 1806 m |

**Key insight:** `Value="36"` with `Unit="second"` gives exactly 500m at 50 km/h — a comfortable urban warning distance. At highway speeds it automatically stretches to 1+ km.

### Time vs Distance — When to Use Which

| Scenario | `Unit="second"` | `Unit="kilometer"` |
|----------|-----------------|-------------------|
| Approaching at zone speed | Triggers at your chosen distance | Same |
| Approaching **faster** than zone speed | Triggers **earlier** — more time to slow down | Same distance — less reaction time |
| Approaching **slower** (traffic, turning) | Triggers **closer** — less unnecessary noise | Same distance — may alert too early |
| Mixed speed limits in one file | Auto-adapts per camera | Same distance for 30 and 120 zones |
| Fixed visual cue on map | Distance varies with speed | Always same distance |

**Recommendation:** Use `"second"` for speed cameras and anything safety-related. Use `"kilometer"` only when you want a fixed geographic trigger radius (e.g., "notify me within 500m of this restaurant").

### Dual Warning Workarounds

**Each waypoint supports exactly one `Activity` element.** You cannot get two alerts (e.g., sound at 500m then visual+sound at 100m) from a single POI entry.

**Possible workarounds:**

1. **Duplicate entries across files** — Create two GPX files with the same POIs but different Activity settings. Whether COMAND fires both alerts for duplicate coordinates is **unconfirmed** — it may deduplicate.

2. **Time-based compromise** — Use `Unit="second" Value="36"` for a single speed-adaptive alert at ~500m (at 50 km/h). This is the practical recommendation.

3. **Split by speed zone** — Use separate files with different Activity settings per speed limit. Each zone gets a warning tuned to its typical driving conditions.

### Common Configurations

**Speed camera (recommended):**
```xml
<gpxd:Activity Active="true" Level="warning" Unit="second" Value="36"/>
```
Full alert, ~500m at 50 km/h, speed-adaptive.

**Long-range highway warning:**
```xml
<gpxd:Activity Active="true" Level="warning" Unit="second" Value="50"/>
```
~1.7 km advance notice at 120 km/h.

**Subtle ping when nearby:**
```xml
<gpxd:Activity Active="true" Level="sound" Unit="kilometer" Value="0.2"/>
```
Audio-only beep at 200m, no visual distraction.

**Quick visual heads-up:**
```xml
<gpxd:Activity Active="true" Level="information" Unit="kilometer" Value="0.05"/>
```
Visual-only at 50m. For POIs you want to see on approach without an audible alert.

**Silent map marker (no alert):**
```xml
<gpxd:Activity Active="false" Level="information" Unit="second" Value="0"/>
```
POI shows on map but never triggers any alert.

---

## Route Format

COMAND supports route files in addition to POI files. Routes use `<gpx:rte>` elements instead of `<gpx:wpt>`.

**Important:** Routes do **not** support the `Activity` element. They cannot trigger alerts. Routes are purely visual — they draw a line on the COMAND map.

```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<gpx:gpx creator="" version="1.1"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:gpx="http://www.topografix.com/GPX/1/1"
  xsi:schemaLocation="http://www.topografix.com/GPX/1/1
    http://www.topografix.com/GPX/1/1/gpx.xsd"
  xmlns:gpxd="http://www.daimler.com/DaimlerGPXExtensions/V2.4">

  <gpx:rte>
    <gpx:name>Route Name</gpx:name>
    <gpx:extensions>
      <gpxd:RteExtension>
        <gpxd:RouteLength Unit="kilometer" Value="2.10"/>
      </gpxd:RteExtension>
    </gpx:extensions>
    <gpx:rtept lat="51.1483" lon="4.9963"/>
    <gpx:rtept lat="51.1482" lon="4.9966"/>
    <gpx:rtept lat="51.1480" lon="4.9970"/>
    <!-- ... ordered waypoints tracing the route -->
  </gpx:rte>

  <!-- more <gpx:rte> elements ... -->

</gpx:gpx>
```

**Route extension elements:**

| Element | Attribute | Description |
|---------|-----------|-------------|
| `RouteLength` | `Unit` | `"kilometer"` or `"mile"` |
| | `Value` | Numeric length of the route |

Route files go in the `Routes/` folder on the SD card, not `PersonalPOI/`.

A single route file can contain multiple `<gpx:rte>` elements.

---

## SD Card Structure

```
SD Card Root/
├── PersonalPOI/
│   ├── speedcams.gpx
│   ├── restaurants.gpx
│   └── ...
└── Routes/
    └── my_routes.gpx
```

**Rules:**

- Folder names are **case-sensitive** on some systems — use exactly `PersonalPOI` and `Routes`
- Multiple `.gpx` files are supported in each folder
- COMAND reads files **live from the SD card** — POIs are not imported to internal storage
- The SD card must remain inserted for POIs to be available
- File names can be anything with a `.gpx` extension
- POI files go in `PersonalPOI/`, route files go in `Routes/`
- **Test your SD card** by putting an MP3 file on it and playing through COMAND first

---

## POI Limits

| Limit | Details |
|-------|---------|
| **Maximum POIs** | **~25,000 - 30,000** total across ALL files on the SD card |
| **Failure mode** | If exceeded, **ALL POIs on the entire SD card are ignored** — not just the excess |
| **Per-file limit** | No known per-file limit (within the total) |
| **Multiple files** | Fully supported |
| **Route limits** | Not well documented — likely generous |

**Warning:** The failure mode is catastrophic. If you exceed the POI limit, COMAND silently ignores every POI on the card. There is no error message. If your POIs suddenly stop working, check the total count across all files.

---

## Observed Behavior and Quirks

These observations come from community testing across various COMAND versions. Your experience may vary with firmware updates.

**Alert triggering:**
- The alert fires **once** per approach — if you stop and reverse back through the trigger zone, it may or may not fire again
- With `Unit="second"`, if you're **stationary** (speed = 0), the alert does **not** fire — it only triggers when moving toward the POI
- Very small `Value` settings (e.g., `"1"` second) may not trigger reliably at high speed due to GPS update frequency (~1 Hz)

**Alert behavior:**
- Alerts are **suppressed** if navigation guidance is actively speaking a turn instruction
- The audible tone volume follows the **navigation audio** volume setting, not the media volume
- The warning appears to be **directional** — it fires when approaching the POI, not when driving away from it (not 100% confirmed across all firmware versions)

**File handling:**
- COMAND reads files on card insertion and when navigation starts — you may need to restart navigation or re-insert the card after updating files
- File names with special characters may cause issues on some firmware versions — stick to ASCII alphanumeric, hyphens, and underscores
- The `creator=""` attribute in the root `<gpx:gpx>` element can be empty — COMAND does not check it

**Format tolerance:**
- COMAND is fairly tolerant of missing elements — a waypoint with only coordinates and a name will work
- Empty `Address` attributes (all `""`) are accepted without issues
- The `gpx:name` element appears to accept quoted strings (with literal `"` in the text content) — community files commonly use this format

---

## XSD Schema History

The original XSD (XML Schema Definition) files were hosted by Daimler:

```
http://www.daimler.com/DaimlerGPXExtensions/V2.4/Daimler_GPX_Extension_V2_4.xsd
http://www.daimler.com/DaimlerGPXExtensions/V2.7.2/Daimler_GPX_Extension_V2_7_2.xsd
http://www.daimler.com/DaimlerGPXExtensions/V2.7.4/Daimler_GPX_Extension_V2_7_4.xsd
```

These URLs are now **dead** (404). The Daimler website has been restructured and the schema files were not migrated. Some third-party tools (like Kurviger) that validated against these schemas broke when the URLs went offline.

The community at MHH AUTO has partially reconstructed the schema from reverse-engineering, but no complete replica is publicly available.

**This is why community documentation like this reference exists** — the only "official" documentation was an XSD file that no longer exists.

---

## Community Sources

The knowledge in this document comes from these community efforts:

### Forum discussions and guides

- [mercedes-forum.com — Import persoenlicher Sonderziele ins COMAND Online NTG 4.5](https://www.mercedes-forum.com/threads/import-persoenlicher-sonderziele-poi-und-routen-ins-comand-online-ntg-4-5.81278/) — Most complete single source: Activity attributes, Level values, Unit types, route format
- [blog.papalima.com — Adding POIs to Mercedes-Benz COMAND / NAVI](http://blog.papalima.com/2017/04/adding-pois-to-mercedes-benz-comand-navi.html) — Practical guide with icon screenshots and SD card setup
- [MHH AUTO — COMAND POI Daimler GPX extensions](https://mhhauto.com/Thread-COMAND-POI-Daimler-gpx-extensions) — Community effort to reconstruct the XSD schema
- [MBClub UK — NAVI personal POI icons for COMAND](https://forums.mbclub.co.uk/threads/navi-personal-poi-icons-for-c0mand.222691/) — Icon identification and testing
- [MBWorld — SatNav / NAVI POI format](https://mbworld.org/forums/s-class-w222/664089-satnav-navi-poi-format.html) — V2.7.4 format discussion for W222 S-Class
- [Kurviger Forum — Importing GPX with Daimler XSD extensions](https://forum.kurviger.com/t/importing-gpx-file-containing-daimler-xsd-extensions-fails-as-xsd-is-missing/12819) — Documentation of the broken XSD URLs

### POI data sources

- [OpenStreetMap](https://www.openstreetmap.org/) via [Overpass API](https://overpass-api.de/) — Speed camera data (ODbL licensed)
- [scdb.info](https://www.scdb.info/) — European speed camera database
- [poi.gps-data-team.com](https://poi.gps-data-team.com/) — Community POI files for various GPS systems

---

## Contributing

If you discover new behavior, elements, or attributes not documented here, please contribute. This format affects thousands of Mercedes owners who want to use personal POIs, and there is no official documentation to turn to.

Areas where community testing is still needed:
- Exact POI limit number (is it 25,000 or 30,000?)
- Whether duplicate coordinates across files trigger multiple alerts
- Route file limits
- Behavior differences between NTG 4.5 and NTG 5
- Whether newer COMAND/MBUX systems use the same format
- The `"sound"` alert level — limited real-world testing
- Directional alert behavior (approach-only or omnidirectional?)
