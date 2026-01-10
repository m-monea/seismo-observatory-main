import json
import os
import math
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen

USGS = "https://earthquake.usgs.gov/fdsnws/event/1/query"

ITALY_BBOX = {
    "min_lat": 35.0,
    "max_lat": 48.5,
    "min_lon": 6.0,
    "max_lon": 19.5,
}


def fetch(days: int = 30, minmag: float = 2.5) -> dict:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    start_s = start.strftime("%Y-%m-%dT%H:%M:%S")
    end_s = end.strftime("%Y-%m-%dT%H:%M:%S")

    url = (
        f"{USGS}?format=geojson"
        f"&starttime={start_s}"
        f"&endtime={end_s}"
        f"&minmagnitude={minmag}"
        f"&orderby=time"
    )

    with urlopen(url) as r:
        payload = json.loads(r.read().decode("utf-8"))

    events = []
    for f in payload.get("features", []):
        p = f.get("properties") or {}
        g = f.get("geometry") or {}
        coords = g.get("coordinates") or []

        lon = lat = depth = None
        if isinstance(coords, list) and len(coords) >= 3:
            lon, lat, depth = coords[0], coords[1], coords[2]

        events.append(
            {
                "id": f.get("id"),
                "time": p.get("time"),
                "mag": p.get("mag"),
                "place": p.get("place"),
                "url": p.get("url"),
                "lat": lat,
                "lon": lon,
                "depth": depth,
            }
        )

    meta = {
        "source": "USGS",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "minmag": minmag,
        "count": len(events),
        "query_url": url,
    }

    return {"meta": meta, "events": events}


def filter_bbox(events, bbox):
    out = []
    for e in events:
        try:
            lat = float(e.get("lat"))
            lon = float(e.get("lon"))
        except Exception:
            continue
        if bbox["min_lat"] <= lat <= bbox["max_lat"] and bbox["min_lon"] <= lon <= bbox["max_lon"]:
            out.append(e)
    return out


def build_grid(events, cell_deg: float = 1.0, min_count_7d: int = 2):
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    day_ms = 24 * 60 * 60 * 1000

    def key_for(lat: float, lon: float):
        i = int((lat + 90.0) // cell_deg)
        j = int((lon + 180.0) // cell_deg)
        return (i, j)

    grid = {}

    for e in events:
        lat = e.get("lat")
        lon = e.get("lon")
        t = e.get("time")
        mag = e.get("mag")

        if lat is None or lon is None or t is None or mag is None:
            continue

        try:
            lat = float(lat)
            lon = float(lon)
            t = int(t)
            mag = float(mag)
        except Exception:
            continue

        age = now_ms - t
        if age > 30 * day_ms:
            continue

        k = key_for(lat, lon)
        cell = grid.get(k)
        if cell is None:
            grid[k] = cell = {"count_7d": 0, "count_30d": 0, "maxmag_30d": None}

        cell["count_30d"] += 1
        cell["maxmag_30d"] = mag if cell["maxmag_30d"] is None else max(cell["maxmag_30d"], mag)
        if age <= 7 * day_ms:
            cell["count_7d"] += 1

    cells = []
    for (i, j), c in grid.items():
        if c["count_7d"] < min_count_7d:
            continue

        lat_min = -90.0 + i * cell_deg
        lat_max = lat_min + cell_deg
        lon_min = -180.0 + j * cell_deg
        lon_max = lon_min + cell_deg

        lambda_7 = (c["count_30d"] / 30.0) * 7.0
        z = (c["count_7d"] - lambda_7) / math.sqrt(lambda_7 + 1.0)

        cells.append(
            {
                "lat_min": lat_min,
                "lat_max": lat_max,
                "lon_min": lon_min,
                "lon_max": lon_max,
                "count_7d": c["count_7d"],
                "count_30d": c["count_30d"],
                "maxmag_30d": c["maxmag_30d"],
                "lambda_7": lambda_7,
                "z": z,
            }
        )

    return cells


def backtest(events, grid_cells, threshold_z=2.5, target_mag=4.5):
    hot = [c for c in grid_cells if c["z"] >= threshold_z]
    if not hot:
        return {"error": "no hot cells"}

    def in_cell(e, c):
        try:
            lat = float(e["lat"])
            lon = float(e["lon"])
        except:
            return False
        return c["lat_min"] <= lat <= c["lat_max"] and c["lon_min"] <= lon <= c["lon_max"]

    large = [e for e in events if (e.get("mag") or 0) >= target_mag]
    if not large:
        return {"large_events": 0}

    hits = 0
    for e in large:
        for c in hot:
            if in_cell(e, c):
                hits += 1
                break

    cell_area = (grid_cells[0]["lat_max"] - grid_cells[0]["lat_min"]) ** 2
    hot_area_frac = len(hot) * cell_area / (180 * 360)
    hit_frac = hits / len(large)

    return {
        "threshold_z": threshold_z,
        "target_mag": target_mag,
        "large_events": len(large),
        "hits_in_hot": hits,
        "hot_area_frac": hot_area_frac,
        "hit_frac": hit_frac,
        "enrichment": hit_frac / hot_area_frac if hot_area_frac > 0 else None,
    }


def atomic_write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


def main():
    os.makedirs("docs", exist_ok=True)

    out = fetch()

    world_grid = build_grid(out["events"], 1.0, 2)
    italy_events = filter_bbox(out["events"], ITALY_BBOX)
    italy_grid = build_grid(italy_events, 0.25, 2)

    bt = backtest(out["events"], world_grid)

    atomic_write("docs/events.json", out)
    atomic_write("docs/grid.json", {"meta": out["meta"], "cells": world_grid})
    atomic_write("docs/italy_events.json", {"meta": out["meta"], "events": italy_events})
    atomic_write("docs/italy_grid.json", {"meta": out["meta"], "cells": italy_grid})
    atomic_write("docs/backtest.json", bt)

    print("OK: data, grids and backtest written")


if __name__ == "__main__":
    main()
