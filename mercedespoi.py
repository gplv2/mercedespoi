#!/usr/bin/env python3
"""
mercedespoi.py — Fetch speed camera data from OpenStreetMap Overpass API
and output Mercedes-Benz COMAND Online compatible GPX (DaimlerGPXExtensions/V2.4).

Replaces the multi-step pipeline (curl → gpsbabel → xmllint → mercedespoi C++)
with a single command. Uses only Python standard library.

Usage:
    ./mercedespoi.py --region belgium -o speedcams.gpx
    ./mercedespoi.py --region antwerp -o antwerp.gpx
    ./mercedespoi.py --input local.json -o offline.gpx
    ./mercedespoi.py --split --region belgium -o speedcams.gpx
"""

import argparse
import json
import math
import os
import re
import sys
import urllib.request
import urllib.error

OVERPASS_API = "https://overpass-api.de/api/interpreter"

# Region definitions: name → Overpass area selector
# Area IDs: 3600000000 + OSM relation ID
# Belgium = 52411, Netherlands = 47796, Luxembourg = 2171347
REGIONS = {
    "belgium": 'area(3600052411)->.searchArea;',
    "netherlands": 'area(3600047796)->.searchArea;',
    "be-nl": '(area(3600052411); area(3600047796);)->.searchArea;',
    "antwerp": 'area["name"="Antwerpen"]["admin_level"="6"]->.searchArea;',
}

COMAND_POI_LIMIT = 30000

# Speed zone definitions for --split mode
# Activity value in seconds — speed-adaptive: triggers N seconds before reaching POI.
SPEED_ZONES = {
    "30":  {"category": "Speedcam 30",  "icon": 6,  "value": "12", "unit": "second"},
    "50":  {"category": "Speedcam 50",  "icon": 6,  "value": "36", "unit": "second"},
    "70":  {"category": "Speedcam 70",  "icon": 6,  "value": "25", "unit": "second"},
    "90":  {"category": "Speedcam 90",  "icon": 16, "value": "20", "unit": "second"},
    "100": {"category": "Speedcam 100", "icon": 16, "value": "18", "unit": "second"},
    "120": {"category": "Speedcam 120", "icon": 16, "value": "18", "unit": "second"},
}
# Default zone for cameras with unknown or unusual maxspeed
DEFAULT_ZONE = {"category": "Speedcam", "icon": 6, "value": "36", "unit": "second"}

# Trajectory (average speed) zone settings
# Entry: full warning (sound + visual) — you're entering an enforced section
# Exit: information only (visual, no sound) — zone has ended
TRAJECTORY_ENTRY = {
    "category": "Trajectory START",
    "icon": 16,       # fixed camera
    "value": "36",    # ~500m at 50, ~600m at 60, ~1000m at 100
    "unit": "second",
    "level": "warning",
}
TRAJECTORY_EXIT = {
    "category": "Trajectory END",
    "icon": 3,        # beach/flag — visually distinct "finish" marker
    "value": "5",     # short: just a brief visual note as you pass the exit
    "unit": "second",
    "level": "information",
}


def normalize_maxspeed(raw):
    """
    Normalize maxspeed tag value to a plain number string, or None if unparseable.

    Handles OSM quirks: "50", "70kmh", "70 kmh", "signals", "variable", "50;30", etc.
    """
    if not raw:
        return None
    m = re.match(r"(\d+)", raw.strip())
    if m:
        return m.group(1)
    return None


def haversine_m(lat1, lon1, lat2, lon2):
    """Distance in meters between two lat/lon points."""
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_query(region):
    """Build Overpass QL query for speed cameras and trajectory controls."""
    area_selector = REGIONS[region]
    return (
        "[out:json][timeout:120];\n"
        f"{area_selector}\n"
        "(\n"
        '  node["highway"="speed_camera"](area.searchArea);\n'
        '  relation["type"="enforcement"]'
        '["enforcement"~"^(maxspeed|average_speed)$"]'
        "(area.searchArea);\n"
        ");\n"
        "(._;>;);\n"
        "out body;\n"
    )


def fetch_overpass(query):
    """POST query to Overpass API, return parsed JSON."""
    data = f"data={query}".encode("utf-8")
    req = urllib.request.Request(
        OVERPASS_API,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
    )
    print("Fetching data from Overpass API...", file=sys.stderr)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"Error: Overpass API returned HTTP {e.code}", file=sys.stderr)
        if e.code == 429:
            print("Rate limited. Wait a moment and try again.", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Could not reach Overpass API: {e.reason}", file=sys.stderr)
        sys.exit(1)
    return json.loads(raw)


def _resolve_entry_exit(members, nodes):
    """
    Resolve entry and exit coordinates for an enforcement relation.

    Tries from/to nodes first, falls back to first/last device nodes.
    Returns (entry_node, exit_node) or (None, None).
    """
    from_ref = None
    to_ref = None
    device_refs = []
    for m in members:
        if m.get("type") != "node":
            continue
        role = m.get("role", "")
        if role == "from":
            from_ref = m["ref"]
        elif role == "to":
            to_ref = m["ref"]
        elif role == "device":
            device_refs.append(m["ref"])

    entry_ref = from_ref or (device_refs[0] if device_refs else None)
    exit_ref = to_ref or (device_refs[-1] if len(device_refs) >= 2 else None)

    entry_node = nodes.get(entry_ref) if entry_ref else None
    exit_node = nodes.get(exit_ref) if exit_ref else None

    # Don't return the same node for both entry and exit
    if entry_node and exit_node and entry_ref == exit_ref:
        exit_node = None

    return entry_node, exit_node


def parse_elements(data):
    """
    Parse Overpass JSON into a list of POI dicts:
        {lat, lon, name, type, maxspeed, ...}

    For average_speed (trajectory) relations, emits TWO POIs: entry and exit,
    each with per-POI overrides for icon, category, and activity settings.

    Pass 1: Index all nodes by ID.
    Pass 2: Extract highway=speed_camera nodes.
    Pass 3: Resolve enforcement relations.
    """
    elements = data.get("elements", [])

    # Pass 1: index nodes by ID
    nodes = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            nodes[el["id"]] = el

    pois = []
    speed_camera_count = 0
    trajectory_count = 0

    # Pass 2: speed_camera nodes
    for el in elements:
        if el.get("type") == "node":
            tags = el.get("tags", {})
            if tags.get("highway") == "speed_camera":
                name = tags.get("name", tags.get("ref", f"node/{el['id']}"))
                pois.append({
                    "lat": el["lat"],
                    "lon": el["lon"],
                    "name": name,
                    "type": "speed_camera",
                    "maxspeed": normalize_maxspeed(tags.get("maxspeed")),
                })
                speed_camera_count += 1

    # Pass 3: enforcement relations
    for el in elements:
        if el.get("type") != "relation":
            continue
        tags = el.get("tags", {})
        if tags.get("type") != "enforcement":
            continue
        enforcement = tags.get("enforcement")
        if enforcement not in ("maxspeed", "average_speed"):
            continue

        members = el.get("members", [])
        maxspeed = normalize_maxspeed(
            tags.get("maxspeed") or tags.get("average_speed")
        )
        base_name = tags.get("name", tags.get("description", f"relation/{el['id']}"))

        if enforcement == "average_speed":
            # Trajectory control: emit entry + exit POIs
            entry_node, exit_node = _resolve_entry_exit(members, nodes)

            # Calculate zone length for the name
            zone_len = ""
            if entry_node and exit_node:
                dist = haversine_m(
                    entry_node["lat"], entry_node["lon"],
                    exit_node["lat"], exit_node["lon"],
                )
                if dist >= 1000:
                    zone_len = f" ({dist / 1000:.1f} km)"
                else:
                    zone_len = f" ({dist:.0f} m)"

            speed_label = f" {maxspeed}" if maxspeed else ""

            if entry_node:
                pois.append({
                    "lat": entry_node["lat"],
                    "lon": entry_node["lon"],
                    "name": f"{base_name}{zone_len}",
                    "type": "trajectory_start",
                    "maxspeed": maxspeed,
                    # Per-POI overrides
                    "icon": TRAJECTORY_ENTRY["icon"],
                    "category": f"Trajectory{speed_label} START",
                    "activity_level": TRAJECTORY_ENTRY["level"],
                    "activity_value": TRAJECTORY_ENTRY["value"],
                    "activity_unit": TRAJECTORY_ENTRY["unit"],
                })

            if exit_node:
                pois.append({
                    "lat": exit_node["lat"],
                    "lon": exit_node["lon"],
                    "name": f"{base_name} END",
                    "type": "trajectory_end",
                    "maxspeed": maxspeed,
                    # Per-POI overrides
                    "icon": TRAJECTORY_EXIT["icon"],
                    "category": f"Trajectory{speed_label} END",
                    "activity_level": TRAJECTORY_EXIT["level"],
                    "activity_value": TRAJECTORY_EXIT["value"],
                    "activity_unit": TRAJECTORY_EXIT["unit"],
                })

            trajectory_count += 1
        else:
            # Point enforcement (maxspeed): single POI at device or from node
            device_ref = None
            from_ref = None
            for m in members:
                if m.get("role") == "device" and m.get("type") == "node":
                    device_ref = m["ref"]
                elif m.get("role") == "from" and m.get("type") == "node":
                    from_ref = m["ref"]

            ref = device_ref or from_ref
            if ref and ref in nodes:
                node = nodes[ref]
                pois.append({
                    "lat": node["lat"],
                    "lon": node["lon"],
                    "name": base_name,
                    "type": "enforcement",
                    "maxspeed": maxspeed,
                })
                speed_camera_count += 1

    return pois, speed_camera_count, trajectory_count


def deduplicate(pois):
    """Deduplicate POIs by coordinate (6 decimal places ≈ 11cm)."""
    seen = set()
    unique = []
    for poi in pois:
        key = (round(poi["lat"], 6), round(poi["lon"], 6))
        if key not in seen:
            seen.add(key)
            unique.append(poi)
    return unique


def xml_escape(s):
    """Escape special XML characters in a string."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def write_mercedes_gpx(pois, output_path, category="Speedcamera", icon_id=6,
                        activity_level="warning", activity_value="50",
                        activity_unit="second"):
    """
    Write Mercedes COMAND Online compatible GPX with DaimlerGPXExtensions/V2.4.

    Per-POI overrides: if a POI dict contains 'icon', 'category', 'activity_level',
    'activity_value', or 'activity_unit', those override the function-level defaults.
    """
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
    lines.append(
        '<gpx:gpx creator="" version="1.1" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:gpx="http://www.topografix.com/GPX/1/1" '
        'xsi:schemaLocation="http://www.topografix.com/GPX/1/1 '
        'http://www.topografix.com/GPX/1/1/gpx.xsd" '
        'xmlns:gpxd="http://www.daimler.com/DaimlerGPXExtensions/V2.4">'
    )

    for poi in pois:
        p_icon = poi.get("icon", icon_id)
        p_cat = xml_escape(poi.get("category", category))
        p_level = poi.get("activity_level", activity_level)
        p_value = poi.get("activity_value", activity_value)
        p_unit = poi.get("activity_unit", activity_unit)
        name = xml_escape(poi["name"])

        lines.append(f'\t<gpx:wpt lat="{poi["lat"]}" lon="{poi["lon"]}">')
        lines.append(f'\t<gpx:name>"{name}"</gpx:name>')
        lines.append(
            "\t\t<gpx:extensions><gpxd:WptExtension>"
            f'<gpxd:WptIconId IconId="{p_icon}"></gpxd:WptIconId>'
        )
        lines.append(f'\t\t<gpxd:POICategory Cat="{p_cat}"></gpxd:POICategory>')
        lines.append(
            f'\t\t<gpxd:Activity Active="true" Level="{p_level}" '
            f'Unit="{p_unit}" Value="{p_value}"></gpxd:Activity>'
        )
        lines.append('\t\t<gpxd:Presentation ShowOnMap="true"></gpxd:Presentation>')
        lines.append(
            '\t\t<gpxd:Address ISO="BE" Country="Belgium" State="" '
            'City="" CityCenter="" Street="" Street2="" HouseNo="" ZIP=""/>'
        )
        lines.append("\t</gpxd:WptExtension>")
        lines.append("\t</gpx:extensions>")
        lines.append("\t</gpx:wpt>")

    lines.append("</gpx:gpx>")

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def _coords_match(a, b, tolerance=1e-7):
    """Check if two (lat, lon) tuples match within tolerance."""
    return abs(a[0] - b[0]) < tolerance and abs(a[1] - b[1]) < tolerance


def chain_way_segments(segments):
    """
    Chain multiple way segments into a continuous route.

    Ways may need to be reversed and reordered to form a continuous path.
    Matches end point of one segment to start point of next.
    """
    if not segments:
        return []
    if len(segments) == 1:
        return list(segments[0])

    chain = list(segments[0])
    remaining = list(segments[1:])

    # Check if first segment needs reversal to connect with next
    if remaining:
        next_seg = remaining[0]
        chain_end = (chain[-1]["lat"], chain[-1]["lon"])
        chain_start = (chain[0]["lat"], chain[0]["lon"])
        next_start = (next_seg[0]["lat"], next_seg[0]["lon"])
        next_end = (next_seg[-1]["lat"], next_seg[-1]["lon"])

        if (not _coords_match(chain_end, next_start)
                and not _coords_match(chain_end, next_end)):
            if (_coords_match(chain_start, next_start)
                    or _coords_match(chain_start, next_end)):
                chain.reverse()

    while remaining:
        chain_end = (chain[-1]["lat"], chain[-1]["lon"])
        found = False

        for i, seg in enumerate(remaining):
            seg_start = (seg[0]["lat"], seg[0]["lon"])
            seg_end = (seg[-1]["lat"], seg[-1]["lon"])

            if _coords_match(chain_end, seg_start):
                chain.extend(seg[1:])  # skip duplicate junction node
                remaining.pop(i)
                found = True
                break
            elif _coords_match(chain_end, seg_end):
                chain.extend(list(reversed(seg))[1:])
                remaining.pop(i)
                found = True
                break

        if not found:
            # Gap in geometry — append remaining segments as-is
            for seg in remaining:
                chain.extend(seg)
            break

    return chain


def parse_trajectory_routes(data):
    """
    Extract route geometry for trajectory (average_speed) enforcement relations.

    Returns a list of route dicts:
        {name, maxspeed, length_m, waypoints: [{lat, lon}, ...]}

    Uses 'section' way members to get road geometry.
    """
    elements = data.get("elements", [])

    # Index nodes by ID
    nodes = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            nodes[el["id"]] = el

    # Index ways by ID
    ways = {}
    for el in elements:
        if el.get("type") == "way":
            ways[el["id"]] = el

    routes = []

    for el in elements:
        if el.get("type") != "relation":
            continue
        tags = el.get("tags", {})
        if tags.get("type") != "enforcement":
            continue
        if tags.get("enforcement") != "average_speed":
            continue

        members = el.get("members", [])
        maxspeed = normalize_maxspeed(
            tags.get("maxspeed") or tags.get("average_speed")
        )
        base_name = tags.get("name", tags.get("description", f"relation/{el['id']}"))

        # Collect section ways in member order
        section_way_ids = [
            m["ref"] for m in members
            if m.get("type") == "way" and m.get("role") == "section"
        ]

        if not section_way_ids:
            continue

        # Resolve ways to ordered coordinate lists
        way_segments = []
        for wid in section_way_ids:
            way = ways.get(wid)
            if not way:
                continue
            node_ids = way.get("nodes", [])
            segment = []
            for nid in node_ids:
                if nid in nodes:
                    n = nodes[nid]
                    segment.append({"lat": n["lat"], "lon": n["lon"]})
            if segment:
                way_segments.append(segment)

        if not way_segments:
            continue

        # Chain segments into continuous route
        waypoints = chain_way_segments(way_segments)

        # Calculate route length from geometry
        length_m = 0.0
        for i in range(1, len(waypoints)):
            length_m += haversine_m(
                waypoints[i - 1]["lat"], waypoints[i - 1]["lon"],
                waypoints[i]["lat"], waypoints[i]["lon"],
            )

        speed_label = f" {maxspeed}" if maxspeed else ""
        routes.append({
            "name": f"Trajectory{speed_label}: {base_name}",
            "maxspeed": maxspeed,
            "length_m": length_m,
            "waypoints": waypoints,
        })

    return routes


def write_trajectory_routes_gpx(routes, output_path):
    """
    Write trajectory zone routes as Mercedes COMAND compatible route GPX.

    Uses <gpx:rte> elements with DaimlerGPXExtensions for route metadata.
    Place the output file in the Routes/ folder on the SD card.
    """
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
    lines.append(
        '<gpx:gpx creator="" version="1.1" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:gpx="http://www.topografix.com/GPX/1/1" '
        'xsi:schemaLocation="http://www.topografix.com/GPX/1/1 '
        'http://www.topografix.com/GPX/1/1/gpx.xsd" '
        'xmlns:gpxd="http://www.daimler.com/DaimlerGPXExtensions/V2.4">'
    )

    for route in routes:
        name = xml_escape(route["name"])
        length_km = route["length_m"] / 1000.0

        lines.append('\t<gpx:rte>')
        lines.append(f'\t\t<gpx:name>{name}</gpx:name>')
        lines.append('\t\t<gpx:extensions>')
        lines.append('\t\t\t<gpxd:RteExtension>')
        lines.append(
            f'\t\t\t\t<gpxd:RouteLength Unit="kilometer" '
            f'Value="{length_km:.2f}"/>'
        )
        lines.append('\t\t\t</gpxd:RteExtension>')
        lines.append('\t\t</gpx:extensions>')

        for wp in route["waypoints"]:
            lines.append(
                f'\t\t<gpx:rtept lat="{wp["lat"]}" lon="{wp["lon"]}"/>'
            )

        lines.append('\t</gpx:rte>')

    lines.append('</gpx:gpx>')

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def group_by_speed(pois):
    """
    Group POIs by their maxspeed value into speed zone buckets.

    Trajectory POIs (type starts with "trajectory_") are grouped separately
    under the "trajectory" key.

    Returns dict: zone_key → list of POIs.
    """
    groups = {}
    for poi in pois:
        if poi["type"].startswith("trajectory_"):
            key = "trajectory"
        else:
            ms = poi.get("maxspeed")
            if ms and ms in SPEED_ZONES:
                key = ms
            else:
                key = "other"
        groups.setdefault(key, []).append(poi)
    return groups


def main():
    parser = argparse.ArgumentParser(
        description="Fetch speed cameras from OpenStreetMap and output "
        "Mercedes COMAND Online compatible GPX."
    )
    parser.add_argument(
        "--region",
        choices=list(REGIONS.keys()),
        default="belgium",
        help="Region to query (default: belgium)",
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        help="Read local Overpass JSON file instead of fetching (offline/debug mode)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="speedcams.gpx",
        help="Output GPX file path (default: speedcams.gpx)",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Split output into separate files per speed limit zone "
        "(speedcams_30.gpx, speedcams_50.gpx, etc.)",
    )
    parser.add_argument(
        "--no-routes",
        action="store_true",
        help="Skip generating trajectory route overlay file",
    )
    args = parser.parse_args()

    # Fetch or load data
    if args.input:
        print(f"Reading local file: {args.input}", file=sys.stderr)
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        query = build_query(args.region)
        data = fetch_overpass(query)

    # Parse
    pois, speed_count, trajectory_count = parse_elements(data)
    total_before = len(pois)

    # Deduplicate
    pois = deduplicate(pois)
    dupes = total_before - len(pois)

    # Count trajectory POIs after dedup
    traj_start = sum(1 for p in pois if p["type"] == "trajectory_start")
    traj_end = sum(1 for p in pois if p["type"] == "trajectory_end")

    # Report stats
    print(f"Speed cameras:       {speed_count}", file=sys.stderr)
    print(f"Trajectory zones:    {trajectory_count} ({traj_start} entry + {traj_end} exit POIs)",
          file=sys.stderr)
    print(f"Duplicates removed:  {dupes}", file=sys.stderr)
    print(f"Total POIs:          {len(pois)}", file=sys.stderr)

    if len(pois) > COMAND_POI_LIMIT:
        print(
            f"WARNING: {len(pois)} POIs exceeds COMAND limit of {COMAND_POI_LIMIT}!",
            file=sys.stderr,
        )

    if args.split:
        # Split mode: one file per speed zone + trajectory file
        groups = group_by_speed(pois)

        out_dir = os.path.dirname(args.output) or "."
        base = os.path.splitext(os.path.basename(args.output))[0]

        print("", file=sys.stderr)
        print("--- Split by speed limit ---", file=sys.stderr)
        total_written = 0

        # Write known speed zones in order
        for zone_key in sorted(SPEED_ZONES.keys(), key=int):
            if zone_key not in groups:
                continue
            zone = SPEED_ZONES[zone_key]
            zone_pois = groups[zone_key]
            filename = f"{base}_{zone_key}.gpx"
            filepath = os.path.join(out_dir, filename)
            write_mercedes_gpx(
                zone_pois, filepath,
                category=zone["category"],
                icon_id=zone["icon"],
                activity_value=zone["value"],
                activity_unit=zone["unit"],
            )
            total_written += len(zone_pois)
            print(
                f"  {filename:30s} {len(zone_pois):5d} POIs  "
                f"(icon={zone['icon']}, warn={zone['value']}s)",
                file=sys.stderr,
            )

        # Write "other" bucket (unknown/unusual maxspeed)
        if "other" in groups:
            other_pois = groups["other"]
            filename = f"{base}_other.gpx"
            filepath = os.path.join(out_dir, filename)
            write_mercedes_gpx(
                other_pois, filepath,
                category=DEFAULT_ZONE["category"],
                icon_id=DEFAULT_ZONE["icon"],
                activity_value=DEFAULT_ZONE["value"],
                activity_unit=DEFAULT_ZONE["unit"],
            )
            total_written += len(other_pois)
            print(
                f"  {filename:30s} {len(other_pois):5d} POIs  "
                f"(icon={DEFAULT_ZONE['icon']}, warn={DEFAULT_ZONE['value']}s)",
                file=sys.stderr,
            )

        # Write trajectory file (entry + exit POIs carry their own overrides)
        if "trajectory" in groups:
            traj_pois = groups["trajectory"]
            filename = f"{base}_trajectory.gpx"
            filepath = os.path.join(out_dir, filename)
            write_mercedes_gpx(traj_pois, filepath)
            total_written += len(traj_pois)
            starts = sum(1 for p in traj_pois if p["type"] == "trajectory_start")
            ends = sum(1 for p in traj_pois if p["type"] == "trajectory_end")
            print(
                f"  {filename:30s} {len(traj_pois):5d} POIs  "
                f"({starts} entry + {ends} exit)",
                file=sys.stderr,
            )

        print(f"  {'':30s} -----", file=sys.stderr)
        print(f"  {'Total':30s} {total_written:5d} POIs", file=sys.stderr)

        if total_written > COMAND_POI_LIMIT:
            print(
                f"\nWARNING: {total_written} total POIs across all files "
                f"exceeds COMAND limit of {COMAND_POI_LIMIT}!",
                file=sys.stderr,
            )
    else:
        # Single file mode
        write_mercedes_gpx(pois, args.output)
        print(f"Written to: {args.output}", file=sys.stderr)

    # Route generation for trajectory zones
    if not args.no_routes and trajectory_count > 0:
        routes = parse_trajectory_routes(data)
        if routes:
            out_dir = os.path.dirname(args.output) or "."
            base = os.path.splitext(os.path.basename(args.output))[0]
            route_filename = f"{base}_routes.gpx"
            route_path = os.path.join(out_dir, route_filename)
            write_trajectory_routes_gpx(routes, route_path)

            total_wps = sum(len(r["waypoints"]) for r in routes)
            print("", file=sys.stderr)
            print("--- Trajectory route overlay ---", file=sys.stderr)
            for r in routes:
                length = r["length_m"]
                if length >= 1000:
                    dist = f"{length / 1000:.1f} km"
                else:
                    dist = f"{length:.0f} m"
                speed = f" [{r['maxspeed']} km/h]" if r.get("maxspeed") else ""
                print(
                    f"  {xml_escape(r['name']):50s} {dist:>8s}{speed}  "
                    f"({len(r['waypoints'])} pts)",
                    file=sys.stderr,
                )
            print(
                f"  {route_filename:50s} {len(routes)} routes, "
                f"{total_wps} waypoints",
                file=sys.stderr,
            )
            print(
                f"  Copy to SD: Routes/{route_filename}",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
