import osmnx as ox
import networkx as nx
import numpy as np
import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.safety_score import predict_safety_score

@st.cache_resource(show_spinner=False)
def load_dhaka_graph():
    graph_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "dhaka_graph.graphml"
    )
    if os.path.exists(graph_path):
        print("Loading saved graph...")
        G = ox.load_graphml(graph_path)
    else:
        print("Downloading graph...")
        G = ox.graph_from_place("Dhaka, Bangladesh", network_type="drive")
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        ox.save_graphml(G, graph_path)
    return G

def geocode_location(location_name):
    try:
        return ox.geocode(location_name + ", Dhaka, Bangladesh")
    except Exception:
        try:
            return ox.geocode(location_name)
        except Exception:
            return None

def get_nearest_node(G, lat, lon):
    return ox.distance.nearest_nodes(G, lon, lat)

def get_safety_weight(highway, hour):
    if isinstance(highway, list):
        highway = highway[0]
    if highway in ['motorway', 'trunk', 'primary']:
        lighting, crowd, crime = 0.85, 0.8, 0.2
    elif highway in ['secondary', 'tertiary']:
        lighting, crowd, crime = 0.7, 0.65, 0.35
    else:
        lighting, crowd, crime = 0.5, 0.45, 0.5
    if hour < 6 or hour >= 22:
        lighting *= 0.5
        crowd   *= 0.2
    score = predict_safety_score(
        hour=hour, crime_rate=crime,
        lighting_score=lighting, crowd_score=crowd,
        hospital_nearby=0, police_nearby=0,
        open_shops=1 if 8 <= hour <= 21 else 0
    )
    return max(1.0, 100.0 - score)

def get_route_info(G, route, hour):
    coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]
    total_time, total_dist, scores = 0, 0, []
    for i in range(len(route) - 1):
        u, v = route[i], route[i+1]
        data = list(G.get_edge_data(u, v).values())[0]
        total_time += data.get('travel_time', 60)
        total_dist += data.get('length', 0)
        w = get_safety_weight(data.get('highway', 'residential'), hour)
        scores.append(100 - (w - 1))
    return {
        "coords": coords,
        "travel_time_min": round(total_time / 60, 1),
        "distance_km":     round(total_dist / 1000, 2),
        "safety_score":    round(float(np.mean(scores)), 1) if scores else 50.0,
        "safety_scores":   scores,
    }

def get_routes(origin_coords, dest_coords, hour):
    try:
        G = load_dhaka_graph()
        orig_node = get_nearest_node(G, origin_coords[0], origin_coords[1])
        dest_node = get_nearest_node(G, dest_coords[0], dest_coords[1])

        # Small bounding box around origin and destination only
        lat1 = min(origin_coords[0], dest_coords[0]) - 0.03
        lat2 = max(origin_coords[0], dest_coords[0]) + 0.03
        lon1 = min(origin_coords[1], dest_coords[1]) - 0.03
        lon2 = max(origin_coords[1], dest_coords[1]) + 0.03

        # Only work with roads inside the bounding box
        relevant_nodes = [n for n, d in G.nodes(data=True)
                         if lat1 <= d['y'] <= lat2 and lon1 <= d['x'] <= lon2]
        subG = G.subgraph(relevant_nodes).copy()

        # Pre-calculate all weights in one pass using vectorized approach
        highway_weights = {
            'motorway': (0.85, 0.8, 0.2),
            'trunk':    (0.85, 0.8, 0.2),
            'primary':  (0.85, 0.8, 0.2),
            'secondary':(0.7,  0.65, 0.35),
            'tertiary': (0.7,  0.65, 0.35),
        }
        night = hour < 6 or hour >= 22
        open_s = 1 if 8 <= hour <= 21 else 0

        # Cache scores for each highway type — only 5 predictions total
        score_cache = {}
        for hw, (lt, cr, cr_rate) in highway_weights.items():
            l = lt * 0.5 if night else lt
            c = cr * 0.2 if night else cr
            score_cache[hw] = predict_safety_score(hour, cr_rate, l, c, 0, 0, open_s)

        default_score = predict_safety_score(
            hour, 0.5,
            0.5 * 0.5 if night else 0.5,
            0.45 * 0.2 if night else 0.45,
            0, 0, open_s
        )

        for u, v, k, data in subG.edges(keys=True, data=True):
            hw = data.get('highway', 'residential')
            if isinstance(hw, list):
                hw = hw[0]
            score = score_cache.get(hw, default_score)
            subG[u][v][k]['safety_weight'] = max(1.0, 100.0 - score) * data.get('length', 1)

        fastest = nx.shortest_path(subG, orig_node, dest_node, weight='travel_time')
        safest  = nx.shortest_path(subG, orig_node, dest_node, weight='safety_weight')

        return {
            "fastest": get_route_info(subG, fastest, hour),
            "safest":  get_route_info(subG, safest,  hour),
        }
    except Exception as e:
        return {"error": str(e)}