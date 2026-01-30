# Coverage Statistics

Speed camera and trajectory control data from OpenStreetMap, fetched via Overpass API.

*Last updated: January 2026*

---

## Country Breakdown

|                          | Belgium | Netherlands | Combined (be-nl) |
|--------------------------|--------:|------------:|------------------:|
| **Speed cameras**        |   1,840 |       1,094 |             2,934 |
| **Trajectory zones**     |     156 |          76 |               230 |
| **Duplicates removed**   |     430 |         219 |               647 |
| **Total POIs**           |   1,708 |       1,027 |             2,733 |
| **Trajectory routes**    |     100 |          76 |               174 |
| **Route geometry points**|   3,399 |       2,630 |             5,951 |

COMAND POI limit: ~30,000. Combined total of 2,733 POIs uses **9%** of capacity.

---

## Trajectory Zone Characteristics

### Netherlands

Dutch trajectory controls are primarily on **motorways and national roads** (A2, A4, A10, A12, A13, A20, N2, N9, N11, N62, N201, N256, N381). Zones tend to be longer, with several exceeding 5 km:

| Zone | Speed | Length |
|------|------:|-------:|
| Trajectcontrole N381 rechts | 100 km/h | 9.3 km |
| Trajectcontrole N381 links | 100 km/h | 9.3 km |
| Trajectcontrole N256 rechts | 80 km/h | 8.9 km |
| Trajectcontrole N256 links | 80 km/h | 8.9 km |
| Trajectcontrole N62 rechts | 100 km/h | 8.0 km |
| Trajectcontrole N62 links | 100 km/h | 8.0 km |
| Trajectcontrole A12 links | 80 km/h | 5.2 km |
| Trajectcontrole A2 rechts | 100 km/h | 5.3 km |
| Trajectcontrole A2 links | 100 km/h | 5.0 km |
| Trajectcontrole A4 rechts | 100 km/h | 4.3 km |

Speed distribution: predominantly **80 km/h** and **100 km/h** zones.

### Belgium

Belgian trajectory controls cover a wider range of road types, from **30 km/h school zones** to **120 km/h motorways**. Zones are generally shorter, reflecting more urban and regional road enforcement:

| Zone | Speed | Length |
|------|------:|-------:|
| relation/13844992 | 120 km/h | 7.7 km |
| Radar troncon vers l'Ouest | 120 km/h | 5.8 km |
| Radar troncon vers l'Est | 120 km/h | 5.6 km |
| relation/13845121 | 120 km/h | 4.7 km |
| N37 Tielt - Ruiselede | 70 km/h | 4.4 km |
| Section Control Route d'Eupen W | 70 km/h | 4.2 km |
| Section Control Route d'Eupen E | 70 km/h | 4.2 km |
| Leupegem naar Berchem | 70 km/h | 3.2 km |
| N37 Ruiselede - Aalter | 70 km/h | 3.1 km |
| relation/16462549 | 70 km/h | 3.6 km |

Speed distribution: wide spread across **30, 50, 70, 90, and 120 km/h** zones. Notably includes 30 km/h school zone enforcement (Bieststraat, etc.) which is uncommon in the Netherlands.

---

## Speed Zone Distribution

### Belgium (--split mode)

| Zone | POIs | Warning | Icon |
|------|-----:|---------|------|
| 30 km/h | 14 | 12s (~100m at 30) | Camera |
| 50 km/h | 41 | 36s (~500m at 50) | Camera |
| 70 km/h | 72 | 25s (~486m at 70) | Camera |
| 90 km/h | 10 | 20s (~500m at 90) | Fixed camera |
| 100 km/h | 2 | 18s (~500m at 100) | Fixed camera |
| 120 km/h | 4 | 18s (~600m at 120) | Fixed camera |
| Other/unknown | 122 | 36s (default) | Camera |
| Trajectory | 72 | Entry: 36s / Exit: 5s | Fixed camera / Flag |

---

## Data Quality Notes

- **Duplicates** occur when a single physical camera is tagged both as a `highway=speed_camera` node and as a member of an `enforcement` relation. Deduplication uses coordinate matching at 6 decimal places (~11 cm precision).
- **Trajectory zones** often appear in pairs (rechts/links, or named directions) representing both sides of the road. This is correct — each direction has its own measured section.
- **"Other/unknown"** includes cameras where OSM contributors didn't tag `maxspeed`, or used non-standard values (`signals`, `variable`, etc.).
- All data is sourced from OpenStreetMap contributors. Coverage depends on local mapping activity. Belgium and the Netherlands both have active OSM communities.

---

## Generating Fresh Stats

```bash
# Belgium only
./mercedespoi.py --region belgium -o speedcams_be.gpx

# Netherlands only
./mercedespoi.py --region netherlands -o speedcams_nl.gpx

# Combined
./mercedespoi.py --region be-nl -o speedcams.gpx

# Combined with split by speed zone
./mercedespoi.py --split --region be-nl -o speedcams.gpx
```
