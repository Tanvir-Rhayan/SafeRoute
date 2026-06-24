import json
import os
import pandas as pd

_places_df = None
_search_index = None

def load_places():
    global _places_df, _search_index
    if _places_df is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path  = os.path.join(base, "data", "dhaka_places.csv")
        json_path = os.path.join(base, "data", "dhaka_search_index.json")
        if not os.path.exists(csv_path):
            return None, []
        _places_df = pd.read_csv(csv_path)
        if os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                _search_index = json.load(f)
        else:
            _search_index = _places_df["name"].tolist()
    return _places_df, _search_index

def search_places(query, limit=8):
    if not query or len(query) < 2:
        return []
    _, index = load_places()
    if not index:
        return []
    q = query.lower()
    starts   = [p for p in index if p.lower().startswith(q)]
    contains = [p for p in index if q in p.lower() and not p.lower().startswith(q)]
    return (starts + contains)[:limit]

def get_place_coords(name):
    df, _ = load_places()
    if df is None:
        return None
    match = df[df["name"] == name]
    if len(match) > 0:
        row = match.iloc[0]
        return (row["lat"], row["lon"])
    return None

def get_nearby_open_places(lat, lon, hour, radius_km=0.5):
    df, _ = load_places()
    if df is None:
        return []
    df = df.copy()
    df["dist"] = ((df["lat"] - lat)**2 + (df["lon"] - lon)**2)**0.5
    nearby = df[df["dist"] < radius_km / 111].copy()
    open_places = []
    for _, row in nearby.iterrows():
        oh = str(row.get("opening_hours", ""))
        if check_open(oh, hour):
            open_places.append({
                "name": row["name"],
                "type": row["type"],
                "lat":  row["lat"],
                "lon":  row["lon"],
                "opening_hours": oh if oh != "nan" else "Open"
            })
    return open_places[:10]

def check_open(oh, hour):
    oh = str(oh).lower().strip()
    if oh in ["", "nan"] or "24/7" in oh or "00:00-24:00" in oh:
        return True
    return 8 <= hour <= 22