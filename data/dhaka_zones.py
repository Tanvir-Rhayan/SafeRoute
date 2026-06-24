import osmnx as ox

DHAKA_ZONES = {
    "Dhanmondi": {"lat": 23.7461, "lon": 90.3742, "base_safety": 75},
    "Gulshan": {"lat": 23.7808, "lon": 90.4152, "base_safety": 82},
    "Mirpur": {"lat": 23.8223, "lon": 90.3654, "base_safety": 50},
    "Uttara": {"lat": 23.8759, "lon": 90.3795, "base_safety": 75},
    "Mohakhali": {"lat": 23.7799, "lon": 90.4043, "base_safety": 55},
    "Motijheel": {"lat": 23.7333, "lon": 90.4170, "base_safety": 52},
    "Old Dhaka": {"lat": 23.7104, "lon": 90.4074, "base_safety": 35},
    "Banani": {"lat": 23.7937, "lon": 90.4066, "base_safety": 78},
    "Bashundhara": {"lat": 23.8134, "lon": 90.4244, "base_safety": 72},
    "Rayer Bazar": {"lat": 23.7562, "lon": 90.3629, "base_safety": 30},
    "Kamalapur": {"lat": 23.7231, "lon": 90.4261, "base_safety": 38},
    "Tejgaon": {"lat": 23.7617, "lon": 90.3933, "base_safety": 55},
    "Badda": {"lat": 23.7795, "lon": 90.4352, "base_safety": 48},
    "Wari": {"lat": 23.7182, "lon": 90.4152, "base_safety": 38},
    "Khilgaon": {"lat": 23.7452, "lon": 90.4318, "base_safety": 48},
    "Shyamoli": {"lat": 23.7706, "lon": 90.3572, "base_safety": 65},
    "Farmgate": {"lat": 23.7583, "lon": 90.3889, "base_safety": 60},
    "Shahbag": {"lat": 23.7394, "lon": 90.3956, "base_safety": 68},
    "Rampura": {"lat": 23.7617, "lon": 90.4318, "base_safety": 50},
    "Malibagh": {"lat": 23.7500, "lon": 90.4200, "base_safety": 48},
    "Mohammadpur": {"lat": 23.7634, "lon": 90.3558, "base_safety": 55},
    "Kafrul": {"lat": 23.7934, "lon": 90.3695, "base_safety": 58},
    "Pallabi": {"lat": 23.8334, "lon": 90.3612, "base_safety": 48},
    "Jatrabari": {"lat": 23.7034, "lon": 90.4318, "base_safety": 35},
    "Demra": {"lat": 23.6934, "lon": 90.4618, "base_safety": 32},
    "Baridhara": {"lat": 23.8034, "lon": 90.4252, "base_safety": 80},
    "Niketan": {"lat": 23.7734, "lon": 90.4052, "base_safety": 72},
    "Panthapath": {"lat": 23.7534, "lon": 90.3852, "base_safety": 62},
    "Azimpur": {"lat": 23.7234, "lon": 90.3852, "base_safety": 55},
    "Cantonment": {"lat": 23.8134, "lon": 90.4052, "base_safety": 85},
}

SAFE_PLACES_24_7 = [
    {"name": "Dhaka Medical College Hospital", "lat": 23.7227, "lon": 90.3969, "type": "hospital"},
    {"name": "Square Hospital", "lat": 23.7512, "lon": 90.3752, "type": "hospital"},
    {"name": "United Hospital", "lat": 23.7957, "lon": 90.4132, "type": "hospital"},
    {"name": "Labaid Hospital", "lat": 23.7498, "lon": 90.3714, "type": "hospital"},
    {"name": "Apollo Hospital", "lat": 23.7934, "lon": 90.4040, "type": "hospital"},
    {"name": "Popular Hospital", "lat": 23.7612, "lon": 90.3812, "type": "hospital"},
    {"name": "Ibn Sina Hospital", "lat": 23.7434, "lon": 90.3734, "type": "hospital"},
    {"name": "Birdem Hospital", "lat": 23.7394, "lon": 90.3956, "type": "hospital"},
    {"name": "Gulshan Police Station", "lat": 23.7806, "lon": 90.4137, "type": "police"},
    {"name": "Dhanmondi Police Station", "lat": 23.7459, "lon": 90.3760, "type": "police"},
    {"name": "Uttara Police Station", "lat": 23.8740, "lon": 90.3850, "type": "police"},
    {"name": "Mirpur Police Station", "lat": 23.8196, "lon": 90.3580, "type": "police"},
    {"name": "Motijheel Police Station", "lat": 23.7330, "lon": 90.4190, "type": "police"},
    {"name": "Tejgaon Police Station", "lat": 23.7620, "lon": 90.3950, "type": "police"},
    {"name": "Mohammadpur Police Station", "lat": 23.7634, "lon": 90.3558, "type": "police"},
    {"name": "Jatrabari Police Station", "lat": 23.7034, "lon": 90.4318, "type": "police"},
    {"name": "Kafrul Police Station", "lat": 23.7934, "lon": 90.3695, "type": "police"},
]

def search_places(query, limit=8):
    """Live search any place in Dhaka using OSMnx geocoder"""
    try:
        results = ox.geocode_to_gdf(query + ", Dhaka, Bangladesh")
        places = []
        for _, row in results.head(limit).iterrows():
            name = row.get("display_name", query)
            short = name.split(",")[0]
            places.append(short)
        return places
    except Exception:
        return []