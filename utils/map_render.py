import folium
from folium.plugins import HeatMap, MiniMap
import numpy as np
from data.dhaka_zones import DHAKA_ZONES, SAFE_PLACES_24_7
from utils.safety_score import get_zone_safety, get_safety_color, get_safety_label
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DHAKA_CENTER = [23.7808, 90.4152]

def create_base_map(night_mode=False):
    tiles = "CartoDB dark_matter" if night_mode else "CartoDB positron"
    m = folium.Map(
        location=DHAKA_CENTER,
        zoom_start=13,
        tiles=tiles,
        prefer_canvas=True
    )
    MiniMap(toggle_display=True).add_to(m)
    return m

def add_routes_to_map(m, fastest_data, safest_data):
    # Fastest route — white/blue
    if fastest_data and "coords" in fastest_data:
        folium.PolyLine(
            locations=fastest_data["coords"],
            color="#4fc3f7",
            weight=5,
            opacity=0.85,
            tooltip=f"⚡ Fastest Route | {fastest_data['travel_time_min']} min | {fastest_data['distance_km']} km",
            popup=folium.Popup(
                f"""<div style='font-family:sans-serif;padding:8px'>
                <b style='color:#4fc3f7'>⚡ Fastest Route</b><br>
                🕐 {fastest_data['travel_time_min']} minutes<br>
                📍 {fastest_data['distance_km']} km<br>
                🛡️ Safety Score: {fastest_data['safety_score']}/100
                </div>""",
                max_width=200
            )
        ).add_to(m)

    # Safest route — green
    if safest_data and "coords" in safest_data:
        folium.PolyLine(
            locations=safest_data["coords"],
            color="#00c96e",
            weight=6,
            opacity=0.9,
            tooltip=f"🛡️ Safest Route | {safest_data['travel_time_min']} min | {safest_data['distance_km']} km",
            popup=folium.Popup(
                f"""<div style='font-family:sans-serif;padding:8px'>
                <b style='color:#00c96e'>🛡️ Safest Route</b><br>
                🕐 {safest_data['travel_time_min']} minutes<br>
                📍 {safest_data['distance_km']} km<br>
                🛡️ Safety Score: {safest_data['safety_score']}/100
                </div>""",
                max_width=200
            )
        ).add_to(m)

    return m

def add_origin_dest_markers(m, origin_coords, dest_coords, origin_name, dest_name):
    # Origin marker
    folium.Marker(
        location=origin_coords,
        popup=f"📍 From: {origin_name}",
        tooltip="Start",
        icon=folium.Icon(color="green", icon="play", prefix="fa")
    ).add_to(m)

    # Destination marker
    folium.Marker(
        location=dest_coords,
        popup=f"🏁 To: {dest_name}",
        tooltip="Destination",
        icon=folium.Icon(color="red", icon="flag", prefix="fa")
    ).add_to(m)
    return m

def add_safe_places(m, hour):
    for place in SAFE_PLACES_24_7:
        is_open = True  # hospitals and police are always open
        icon_color = "blue" if place["type"] == "hospital" else "darkblue"
        icon_name = "plus" if place["type"] == "hospital" else "shield"

        folium.Marker(
            location=[place["lat"], place["lon"]],
            popup=folium.Popup(
                f"""<div style='font-family:sans-serif;padding:6px'>
                <b>{place['name']}</b><br>
                {'🏥 Hospital' if place['type'] == 'hospital' else '🚔 Police Station'}<br>
                <span style='color:green'>✅ Open 24/7</span>
                </div>""",
                max_width=180
            ),
            tooltip=place["name"],
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
        ).add_to(m)
    return m

def add_zone_circles(m, hour):
    for zone_name, zone_data in DHAKA_ZONES.items():
        crime_map = {
            "Dhanmondi": 0.2, "Gulshan": 0.15, "Mirpur": 0.45,
            "Uttara": 0.25, "Mohakhali": 0.4, "Motijheel": 0.35,
            "Old Dhaka": 0.5, "Banani": 0.2, "Bashundhara": 0.22,
            "Rayer Bazar": 0.55, "Kamalapur": 0.5, "Tejgaon": 0.38,
            "Badda": 0.42, "Wari": 0.45, "Khilgaon": 0.4, "Shyamoli": 0.3
        }
        zone_info = {
            "crime_rate": crime_map.get(zone_name, 0.4),
            "lighting_day": 0.75,
            "crowd_day": 0.7,
            "hospital_nearby": 1 if zone_name in ["Dhanmondi", "Gulshan", "Banani", "Uttara", "Bashundhara"] else 0,
            "police_nearby": 1 if zone_name in ["Dhanmondi", "Gulshan", "Uttara", "Mirpur", "Motijheel", "Tejgaon"] else 0,
        }
        score = get_zone_safety(zone_info, hour)
        color = get_safety_color(score)
        label = get_safety_label(score)

        folium.Circle(
            location=[zone_data["lat"], zone_data["lon"]],
            radius=600,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.25,
            popup=folium.Popup(
                f"""<div style='font-family:sans-serif;padding:8px'>
                <b>{zone_name}</b><br>
                🛡️ Safety Score: <b>{score}/100</b><br>
                Status: <b style='color:{color}'>{label}</b><br>
                🕐 At {hour:02d}:00
                </div>""",
                max_width=180
            ),
            tooltip=f"{zone_name}: {score}/100 ({label})"
        ).add_to(m)
    return m

def create_heatmap(hour):
    m = create_base_map(night_mode=True)
    heat_data = []
    crime_map = {
        "Dhanmondi": 0.2, "Gulshan": 0.15, "Mirpur": 0.45,
        "Uttara": 0.25, "Mohakhali": 0.4, "Motijheel": 0.35,
        "Old Dhaka": 0.5, "Banani": 0.2, "Bashundhara": 0.22,
        "Rayer Bazar": 0.55, "Kamalapur": 0.5, "Tejgaon": 0.38,
        "Badda": 0.42, "Wari": 0.45, "Khilgaon": 0.4, "Shyamoli": 0.3
    }

    for zone_name, zone_data in DHAKA_ZONES.items():
        zone_info = {
            "crime_rate": crime_map.get(zone_name, 0.4),
            "lighting_day": 0.75,
            "crowd_day": 0.7,
            "hospital_nearby": 1 if zone_name in ["Dhanmondi", "Gulshan", "Banani", "Uttara", "Bashundhara"] else 0,
            "police_nearby": 1 if zone_name in ["Dhanmondi", "Gulshan", "Uttara", "Mirpur", "Motijheel", "Tejgaon"] else 0,
        }
        score = get_zone_safety(zone_info, hour)
        # Invert for heatmap: high danger = high heat
        danger = (100 - score) / 100
        heat_data.append([zone_data["lat"], zone_data["lon"], danger])

    HeatMap(
        heat_data,
        min_opacity=0.4,
        max_zoom=18,
        radius=80,
        blur=60,
        gradient={0.2: '#00c96e', 0.5: '#f5a623', 0.8: '#e63946'}
    ).add_to(m)
    return m

def add_legend(m, night_mode=False):
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: rgba(15,17,23,0.92); border-radius: 12px;
                padding: 14px 18px; font-family: sans-serif; font-size: 13px;
                border: 1px solid #2a2d3a; color: #fff; min-width: 160px;">
        <div style="font-weight:700; margin-bottom:10px; color:#fff;">Map Legend</div>
        <div style="margin:5px 0"><span style="color:#00c96e">●</span> Safe Zone (65–100)</div>
        <div style="margin:5px 0"><span style="color:#f5a623">●</span> Moderate (40–64)</div>
        <div style="margin:5px 0"><span style="color:#e63946">●</span> Unsafe (0–39)</div>
        <hr style="border-color:#2a2d3a; margin:8px 0">
        <div style="margin:5px 0"><span style="color:#00c96e">━━</span> Safest Route</div>
        <div style="margin:5px 0"><span style="color:#4fc3f7">━━</span> Fastest Route</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m