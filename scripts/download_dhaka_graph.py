import osmnx as ox
import os

print("Downloading Dhaka road network...")
print("This takes 2-3 minutes. Run only once.")

G = ox.graph_from_place("Dhaka, Bangladesh", network_type="drive")
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

os.makedirs("data", exist_ok=True)
ox.save_graphml(G, "data/dhaka_graph.graphml")

print(f"Saved! Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
print("App will now load in 3 seconds instead of 3 minutes.")