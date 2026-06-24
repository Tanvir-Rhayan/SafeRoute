import pandas as pd
import joblib
import numpy as np
import os
import json


# Load model once
_model = None
_metrics = None

def load_model():
    global _model, _metrics
    if _model is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "model", "safety_model.pkl")
        metrics_path = os.path.join(base_dir, "model", "metrics.json")
        _model = joblib.load(model_path)
        with open(metrics_path) as f:
            _metrics = json.load(f)
    return _model, _metrics

def predict_safety_score(hour, crime_rate, lighting_score, crowd_score,
                          hospital_nearby, police_nearby, open_shops):
    model, _ = load_model()
    features = pd.DataFrame([[hour, crime_rate, lighting_score, crowd_score,
                               hospital_nearby, police_nearby, open_shops]],
                             columns=["hour", "crime_rate", "lighting_score",
                                      "crowd_score", "hospital_nearby",
                                      "police_nearby", "open_shops"])
    score = model.predict(features)[0]
    return round(float(np.clip(score, 0, 100)), 1)

def get_zone_safety(zone_data, hour, nearby_open_count=0):
    """Calculate safety score — now uses real nearby open places"""
    if 6 <= hour <= 20:
        open_shops = 1
        crowd_score = zone_data.get("crowd_day", 0.7)
        lighting_score = zone_data.get("lighting_day", 0.8)
    elif 20 <= hour <= 22:
        open_shops = 1 if nearby_open_count > 3 else 0
        crowd_score = zone_data.get("crowd_day", 0.7) * 0.6
        lighting_score = zone_data.get("lighting_day", 0.8) * 0.75
    else:
        open_shops = 1 if nearby_open_count > 5 else 0
        crowd_score = 0.15
        lighting_score = zone_data.get("lighting_day", 0.8) * 0.4

    score = predict_safety_score(
        hour=hour,
        crime_rate=zone_data.get("crime_rate", 0.4),
        lighting_score=lighting_score,
        crowd_score=crowd_score,
        hospital_nearby=zone_data.get("hospital_nearby", 0),
        police_nearby=zone_data.get("police_nearby", 0),
        open_shops=open_shops
    )
    return score

def get_safety_color(score):
    if score >= 65:
        return "#00c96e"  # green
    elif score >= 40:
        return "#f5a623"  # yellow
    else:
        return "#e63946"  # red

def get_safety_label(score):
    if score >= 65:
        return "Safe"
    elif score >= 40:
        return "Moderate"
    else:
        return "Unsafe"

def get_route_safety_summary(scores):
    avg = np.mean(scores)
    unsafe_count = sum(1 for s in scores if s < 40)
    moderate_count = sum(1 for s in scores if 40 <= s < 65)
    safe_count = sum(1 for s in scores if s >= 65)
    return {
        "average": round(float(avg), 1),
        "unsafe_zones": unsafe_count,
        "moderate_zones": moderate_count,
        "safe_zones": safe_count,
        "label": get_safety_label(avg),
        "color": get_safety_color(avg)
    }