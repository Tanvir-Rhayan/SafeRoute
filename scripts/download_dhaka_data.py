import osmnx as ox
import pandas as pd
import os
import json

print("Downloading all Dhaka places from OpenStreetMap...")
print("This will take 3-5 minutes. Run only once.")

# Download all points of interest in Dhaka
tags = {
    "amenity": [
        "hospital", "clinic", "pharmacy", "police", "fire_station",
        "school", "college", "university", "mosque", "temple", "church",
        "restaurant", "cafe", "fast_food", "bank", "atm",
        "fuel", "parking", "bus_station", "marketplace"
    ],
    "shop": True,       # all shops
    "building": [
        "commercial", "retail", "supermarket", "mall"
    ]
}

gdf = ox.features_from_place("Dhaka, Bangladesh", tags=tags)

print(f"Total places found: {len(gdf)}")

# Clean and extract useful columns
places = []
for idx, row in gdf.iterrows():
    name = row.get("name", None)
    if not name or str(name) == "nan":
        continue

    # Get coordinates
    try:
        geom = row.geometry
        if geom.geom_type == "Point":
            lat, lon = geom.y, geom.x
        else:
            lat, lon = geom.centroid.y, geom.centroid.x
    except Exception:
        continue

    # Get place type
    amenity = str(row.get("amenity", ""))
    shop    = str(row.get("shop", ""))
    building= str(row.get("building", ""))

    if amenity and amenity != "nan":
        place_type = amenity
    elif shop and shop != "nan":
        place_type = f"shop_{shop}"
    elif building and building != "nan":
        place_type = f"building_{building}"
    else:
        place_type = "place"

    # Opening hours
    opening_hours = str(row.get("opening_hours", ""))

    places.append({
        "name": str(name),
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "type": place_type,
        "opening_hours": opening_hours if opening_hours != "nan" else ""
    })

df = pd.DataFrame(places)
df = df.drop_duplicates(subset=["name", "lat", "lon"])
df = df.sort_values("name")

print(f"Clean places saved: {len(df)}")

# Save
os.makedirs("data", exist_ok=True)
df.to_csv("data/dhaka_places.csv", index=False)

# Also save as searchable JSON
search_list = df["name"].tolist()
with open("data/dhaka_search_index.json", "w", encoding="utf-8") as f:
    json.dump(search_list, f, ensure_ascii=False)

print("Saved to data/dhaka_places.csv")
print("Saved to data/dhaka_search_index.json")
print("Done! You now have all Dhaka locations.")