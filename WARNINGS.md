# COMAND Online Warning Behavior — Technical Reference

How Mercedes-Benz COMAND Online (NTG 4.5 / NTG 5) alerts you when approaching a Personal POI. All of this is controlled by the `<gpxd:Activity>` element in the DaimlerGPXExtensions GPX format.

---

## The Activity Element

```xml
<gpxd:Activity Active="true" Level="warning" Unit="second" Value="36"></gpxd:Activity>
```

Four attributes control the alert:

| Attribute | Required | Description |
|-----------|----------|-------------|
| `Active` | Yes | `"true"` to enable, `"false"` to disable the alert entirely |
| `Level` | Yes | Type of alert — determines what you see and hear |
| `Unit` | Yes | How the trigger distance is measured |
| `Value` | Yes | The trigger distance/time — numeric, supports decimals |

---

## Alert Levels

The `Level` attribute determines what happens when you enter the trigger zone.

### `Level="warning"` — Visual + Audio

The most noticeable option. COMAND displays a visual popup **and** plays an audible alert tone. Use this for anything you really need to notice (speed cameras).

### `Level="information"` — Visual Only

A visual indicator appears on the map (the POI icon highlights or a notification shows), but no sound is played. Useful for points of interest you want to see on the map but don't need an audible alert for (restaurants, hotels, parking).

### `Level="sound"` — Audio Only

An audible tone plays, but no visual popup appears. This is the subtlest active alert — a brief notification you hear but that doesn't change the map display.

### Summary

| Level | Visual popup | Audio tone | Best for |
|-------|-------------|------------|----------|
| `"warning"` | Yes | Yes | Speed cameras, critical alerts |
| `"information"` | Yes | No | Interesting locations, non-urgent POIs |
| `"sound"` | No | Yes | Subtle advance notice |

---

## Trigger Units

The `Unit` attribute determines how COMAND calculates when to fire the alert.

### `Unit="second"` — Time-Based (Speed-Adaptive)

The alert fires **N seconds before you reach the POI** at your current speed. This is the key insight: the trigger distance scales automatically with your speed.

**Formula:** `distance = speed × value / 3.6`

where speed is in km/h, value is in seconds, and distance is in meters.

#### Conversion Table — Seconds to Meters

| Value | 30 km/h | 50 km/h | 70 km/h | 90 km/h | 100 km/h | 120 km/h | 130 km/h |
|-------|---------|---------|---------|---------|----------|----------|----------|
| 5 | 42 m | 69 m | 97 m | 125 m | 139 m | 167 m | 181 m |
| 9 | 75 m | 125 m | 175 m | 225 m | 250 m | 300 m | 325 m |
| 12 | 100 m | 167 m | 233 m | 300 m | 333 m | 400 m | 433 m |
| 18 | 150 m | 250 m | 350 m | 450 m | 500 m | 600 m | 650 m |
| 20 | 167 m | 278 m | 389 m | 500 m | 556 m | 667 m | 722 m |
| 25 | 208 m | 347 m | 486 m | 625 m | 694 m | 833 m | 903 m |
| 30 | 250 m | 417 m | 583 m | 750 m | 833 m | 1000 m | 1083 m |
| 36 | 300 m | 500 m | 700 m | 900 m | 1000 m | 1200 m | 1300 m |
| 50 | 417 m | 694 m | 972 m | 1250 m | 1389 m | 1667 m | 1806 m |

**Why this matters:** If you're doing 50 km/h in a 30 zone and the warning is set to 12 seconds, you get alerted at 167m instead of 100m. The system adapts to your actual approach speed — you always get the same amount of reaction time regardless of how fast you're going.

### `Unit="kilometer"` — Fixed Distance (km)

The alert fires at a fixed distance from the POI, regardless of your speed.

| Value | Distance |
|-------|----------|
| `"0.05"` | 50 m |
| `"0.1"` | 100 m |
| `"0.2"` | 200 m |
| `"0.3"` | 300 m |
| `"0.5"` | 500 m |
| `"1"` | 1000 m |
| `"1.5"` | 1500 m |
| `"2"` | 2000 m |

Decimal values are supported (`"0.5"` = 500 meters).

### `Unit="mile"` — Fixed Distance (miles)

Same as kilometer but in miles. Presumably for UK/US use.

| Value | Distance |
|-------|----------|
| `"0.1"` | ~161 m |
| `"0.25"` | ~402 m |
| `"0.5"` | ~805 m |
| `"1"` | ~1609 m |

### Which Unit Should You Use?

**`"second"` is almost always the better choice for speed cameras.** Here's why:

| Scenario | `Unit="second"` | `Unit="kilometer"` |
|----------|-----------------|-------------------|
| Approaching at zone speed | Triggers at your chosen distance | Same |
| Approaching faster than zone speed | Triggers **earlier** — more time to slow down | Triggers at same distance — less time |
| Approaching slower (traffic, turning) | Triggers **closer** — less unnecessary noise | Triggers far away — possibly annoying |
| Highway vs. urban in same file | Auto-adapts per camera | Same distance for 30 and 120 zones |

The only scenario where fixed distance (`"kilometer"`) wins is when you always want the same visual cue on the map regardless of speed — for example, "highlight this restaurant when I'm within 500m."

---

## The mercedespoi.py Speed Zone Tuning

The `--split` mode in `mercedespoi.py` assigns different warning values per speed zone. Here's the design rationale.

### Design Goal

Give roughly **500m of warning at the zone's speed limit**, with adjustments:
- Urban 30 km/h zones get a shorter warning (100m) — cameras are close together in residential areas, long warnings would overlap and become noise
- Urban 50 km/h zones get the full 500m — the standard urban speed, most common zone
- Highway 90+ zones aim for 500-600m — adequate at higher speeds

### Zone Configuration

```python
SPEED_ZONES = {
    "30":  {"value": "12", "unit": "second"},   #  30 km/h × 12s / 3.6 = 100m
    "50":  {"value": "36", "unit": "second"},   #  50 km/h × 36s / 3.6 = 500m
    "70":  {"value": "25", "unit": "second"},   #  70 km/h × 25s / 3.6 = 486m
    "90":  {"value": "20", "unit": "second"},   #  90 km/h × 20s / 3.6 = 500m
    "100": {"value": "18", "unit": "second"},   # 100 km/h × 18s / 3.6 = 500m
    "120": {"value": "18", "unit": "second"},   # 120 km/h × 18s / 3.6 = 600m
}
DEFAULT_ZONE = {"value": "36", "unit": "second"}  # Unknown → same as 50 km/h
```

### What You Actually Experience

| Zone | At zone speed | Going 10 over | Going 20 over | In traffic (20 km/h) |
|------|--------------|---------------|---------------|---------------------|
| **30 km/h** (12s) | 100 m | 133 m | 167 m | 67 m |
| **50 km/h** (36s) | 500 m | 600 m | 700 m | 200 m |
| **70 km/h** (25s) | 486 m | 556 m | 625 m | 139 m |
| **90 km/h** (20s) | 500 m | 556 m | 611 m | 111 m |
| **100 km/h** (18s) | 500 m | 550 m | 600 m | 100 m |
| **120 km/h** (18s) | 600 m | 650 m | 700 m | 100 m |

Notice the speed-adaptive behavior: if you're doing 60 in a 50 zone, the 36-second warning fires at 600m instead of 500m — giving you extra time to react precisely when you need it most.

### Customizing the Zones

Edit the `SPEED_ZONES` dict at the top of `mercedespoi.py`. Each zone has:

```python
"50": {
    "category": "Speedcam 50",  # POICategory shown in COMAND
    "icon": 6,                   # IconId (6=mobile cam, 16=fixed cam)
    "value": "36",               # Activity Value
    "unit": "second",            # Activity Unit
}
```

Some examples of alternative tuning:

**Aggressive (early warnings everywhere):**
```python
"50":  {"category": "Speedcam 50",  "icon": 6,  "value": "54", "unit": "second"},  # 750m at 50
"120": {"category": "Speedcam 120", "icon": 16, "value": "30", "unit": "second"},  # 1000m at 120
```

**Minimal (late, subtle warnings):**
```python
"50":  {"category": "Speedcam 50",  "icon": 6,  "value": "18", "unit": "second"},  # 250m at 50
"120": {"category": "Speedcam 120", "icon": 16, "value": "9",  "unit": "second"},  # 300m at 120
```

**Fixed distance (ignoring speed):**
```python
"50":  {"category": "Speedcam 50",  "icon": 6,  "value": "0.5", "unit": "kilometer"},  # always 500m
"120": {"category": "Speedcam 120", "icon": 16, "value": "1",   "unit": "kilometer"},  # always 1km
```

---

## Can You Get Two Warnings per Camera?

**Short answer: not with a single POI entry.** Each `<gpx:wpt>` supports exactly one `<gpxd:Activity>` element.

### The Idea

You might want: a subtle sound at 500m to prepare, then a full visual+audio warning at 100m for the final approach.

### Workaround: Duplicate Entries Across Files

Create two GPX files with the same cameras but different Activity settings:

**File 1 — `speedcams_early.gpx` (sound at 500m):**
```xml
<gpxd:Activity Active="true" Level="sound" Unit="kilometer" Value="0.5"/>
```

**File 2 — `speedcams_close.gpx` (warning at 100m):**
```xml
<gpxd:Activity Active="true" Level="warning" Unit="kilometer" Value="0.1"/>
```

**Status: Untested.** Whether COMAND fires alerts for both entries at the same coordinates is unknown. Possible outcomes:
1. Both fire — you get the desired two-stage alert (best case)
2. COMAND deduplicates by coordinate — only one fires (likely)
3. Both appear on the map but only one alert fires (possible)

If you try this, consider that it doubles your POI count. Belgium's ~1,580 cameras would become ~3,160 — still well within the 30K limit.

### Practical Alternative: Time-Based Compromise

Instead of two triggers, use a single `Level="warning"` (sound + visual) with `Unit="second"` tuned so the alert fires at a comfortable advance distance. `Value="36"` gives:
- ~500m at 50 km/h (plenty of time in urban areas)
- ~1200m at 120 km/h (early notice on highways)

This is what `--split` mode does by default — each zone is tuned for its typical driving conditions.

---

## Common Activity Configurations

### Speed cameras (recommended)
```xml
<gpxd:Activity Active="true" Level="warning" Unit="second" Value="36"/>
```
Full alert, ~500m at 50 km/h, speed-adaptive.

### Silent map marker (no alert)
```xml
<gpxd:Activity Active="false" Level="information" Unit="second" Value="0"/>
```
POI shows on map but never triggers any alert.

### Subtle ping when nearby
```xml
<gpxd:Activity Active="true" Level="sound" Unit="kilometer" Value="0.2"/>
```
Audio-only beep at 200m. No visual distraction.

### Long-range highway warning
```xml
<gpxd:Activity Active="true" Level="warning" Unit="second" Value="50"/>
```
Alert 50 seconds before reaching POI. At 120 km/h that's 1,667m — almost 2km advance notice.

### Quick heads-up at close range
```xml
<gpxd:Activity Active="true" Level="information" Unit="kilometer" Value="0.05"/>
```
Visual-only notification at 50m. For POIs you want to see on approach but don't need an audible alert for.

---

## Trajectory Controls (Average Speed Zones)

Trajectory controls ("trajectcontrole" in Belgium/Netherlands) measure your **average speed over a section** of road, not your instantaneous speed at one point. Two or more cameras record your license plate and timestamp at entry and exit; if the average speed exceeds the limit, you're fined.

**This changes everything about warning strategy.** A point camera warning is "brake now." A trajectory warning is "maintain speed for the next 1-3 km."

### The Problem With Point Warnings

A single POI alert at a trajectory camera is misleading. If you only get warned at the start camera, you might slow down there and speed up again — but the system is measuring your *average*, so that doesn't help. You need to know:

1. Where the zone **starts** — so you begin maintaining the correct speed
2. Where the zone **ends** — so you know when you can resume normal driving
3. How **long** the zone is — to understand how long you need to maintain speed

### How mercedespoi.py Handles Trajectories

The script emits **two POIs per trajectory zone**: entry and exit.

#### Entry POI (zone start)

```xml
<gpx:name>"Trajectcontrole N141 (630 m)"</gpx:name>
<gpxd:WptIconId IconId="16"/>           <!-- fixed camera icon -->
<gpxd:POICategory Cat="Trajectory 70 START"/>
<gpxd:Activity Active="true" Level="warning" Unit="second" Value="36"/>
```

- **Icon:** `IconId="16"` — fixed camera. Visually distinct from mobile cameras (`IconId="6"`)
- **Category:** `"Trajectory {speed} START"` — includes the maxspeed and "START" label, so you can filter by category in COMAND
- **Alert:** `Level="warning"` — **full sound + visual alert**. You need to notice this one. At 70 km/h with `Value="36"`, you're warned ~700m before the entry camera
- **Name:** includes the zone length in parentheses, e.g., `"Trajectcontrole N141 (630 m)"`, so when you look at the POI details you know how long to maintain speed

#### Exit POI (zone end)

```xml
<gpx:name>"Trajectcontrole N141 END"</gpx:name>
<gpxd:WptIconId IconId="3"/>            <!-- beach/flag icon -->
<gpxd:POICategory Cat="Trajectory 70 END"/>
<gpxd:Activity Active="true" Level="information" Unit="second" Value="5"/>
```

- **Icon:** `IconId="3"` — beach/flag marker. Visually distinct from camera icons — this is a "finish line" marker, not a threat
- **Category:** `"Trajectory {speed} END"` — separate category from START, so you could hide exit markers if you only want to see entries
- **Alert:** `Level="information"` — **visual only, no sound**. A quiet visual note that the zone has ended. No beep needed — you just want to know you can relax
- **Value:** `"5"` seconds — brief, just as you pass the exit camera

### Why These Specific Choices

| Decision | Rationale |
|----------|-----------|
| `IconId="16"` for entry | Fixed camera icon — trajectory cameras are fixed installations. Matches the real-world object |
| `IconId="3"` for exit | Beach/flag icon — visually different from any camera icon. Acts as a "finish flag" |
| `Level="warning"` for entry | You MUST notice the zone start — full audio + visual |
| `Level="information"` for exit | No urgency — just a visual "you're clear" signal. No sound needed |
| `Value="36"` for entry | ~500m at 50, ~700m at 70, ~1000m at 100 — enough distance to adjust speed before entering |
| `Value="5"` for exit | Very short — you just want to see the icon flash as you pass the exit point |
| Zone length in name | When you tap the POI in COMAND, you see e.g., "(630 m)" — so you know how long to hold your speed |
| Separate START/END categories | You can toggle visibility per category in COMAND — show entries but hide exits if you prefer a cleaner map |

### Zone Data from OSM

Trajectory relations in OpenStreetMap have this structure:

```
relation (type=enforcement, enforcement=average_speed)
├── from: node — start of measured section
├── to: node — end of measured section
├── device: node(s) — physical camera locations
└── section: way(s) — the road segments between cameras
```

The script uses `from`/`to` nodes for coordinates when available, falling back to the first/last `device` nodes. Zone length is calculated as the straight-line distance between entry and exit (actual road distance may be slightly longer on curved roads).

### Typical Zone Lengths (Belgium)

Based on Antwerp province data (55 trajectory zones):

| Range | Count | Examples |
|-------|-------|---------|
| < 500 m | 4 | Short urban sections |
| 500 m - 1 km | 24 | Typical urban/suburban trajectories |
| 1 - 2 km | 17 | Suburban/interurban roads |
| 2 - 3 km | 8 | Longer highway sections |
| > 3 km | 2 | Extended highway monitoring |

Most zones are 500m to 2km. At 70 km/h, that's 26 to 103 seconds of maintained speed.

### Split Mode Output

In `--split` mode, trajectory POIs get their own dedicated file:

```
speedcams_trajectory.gpx          72 POIs  (33 entry + 39 exit)
```

Entry and exit POIs are interleaved in the file. Each carries its own icon, category, and activity settings as per-POI overrides, so a single file contains both the loud entry warnings and the quiet exit notifications.

### Route Overlay (Implemented)

The tool now generates a route overlay file alongside the POI alerts. This gives you the best of both worlds:

| Layer | Purpose | File location |
|---|---|---|
| **POI alerts** | Sound at zone entry (36s ahead), visual at zone exit | `PersonalPOI/` |
| **Route overlay** | Visible line on map showing the exact measured section | `Routes/` |

The route file uses `<gpx:rte>` elements with `<gpx:rtept>` waypoints tracing the actual road geometry from OSM section ways. Each trajectory zone becomes a named route with its total length in the `RouteLength` extension.

Routes don't support the `Activity` element — no alerts. That's why both layers are needed. The route overlay lets you see an upcoming trajectory zone on the map from a distance, well before the 36-second entry alert fires.

**Belgium stats:** ~100 routes, ~3,400 geometry waypoints. Generated automatically unless `--no-routes` is passed.

The route file is named `{basename}_routes.gpx` (e.g., `speedcams_routes.gpx`) and should be copied to the `Routes/` folder on the SD card.

---

## Observed Behavior Notes

These observations come from community testing (sources listed below). Your mileage may vary across COMAND versions and firmware updates.

- The alert fires **once** per approach — if you stop and reverse back through the trigger zone, it may or may not fire again
- With `Unit="second"`, if you're stationary (speed = 0), the alert does not fire — it only triggers when you're moving toward the POI
- Alerts are suppressed if navigation guidance is actively speaking a turn instruction
- The audible tone volume follows the navigation audio volume setting
- Very small `Value` settings (e.g., `"1"` second) may not trigger reliably at high speed due to GPS update frequency
- The warning seems to be directional — it fires when you're approaching the POI, not when driving away from it (not 100% confirmed)

---

## Sources

- [mercedes-forum.com — NTG 4.5 POI import](https://www.mercedes-forum.com/threads/import-persoenlicher-sonderziele-poi-und-routen-ins-comand-online-ntg-4-5.81278/) — Activity element attributes, Level values, Unit types
- [blog.papalima.com — Adding POIs to COMAND](http://blog.papalima.com/2017/04/adding-pois-to-mercedes-benz-comand-navi.html) — practical testing
- [MHH AUTO — COMAND POI Daimler GPX extensions](https://mhhauto.com/Thread-COMAND-POI-Daimler-gpx-extensions) — reverse-engineering the XSD schema
- [MBClub UK forums](https://forums.mbclub.co.uk/threads/navi-personal-poi-icons-for-c0mand.222691/) — icon and alert testing
