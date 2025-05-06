import networkx as nx
from sklearn.neighbors import BallTree
import numpy as np
import re
import plotly.graph_objects as go
from graph_loader import haversine_distance

# ---------------------- Optimized Subgraph Builder ----------------------

def build_subgraph(G, tree, node_array, a_star_path, radius_km=700):
    """Efficient subgraph construction around A* path"""
    earth_radius_km = 6371
    radius_rad = radius_km / earth_radius_km
    subgraph_nodes = set()
    node_list = list(G.nodes())

    for lon, lat in a_star_path:
        query_rad = np.radians([[lat, lon]])  # BallTree expects (lat, lon)
        indices = tree.query_radius(query_rad, r=radius_rad)[0]

        # Vectorized distance calculation
        candidates = node_array[indices]
        distances = haversine_distance(lat, lon, candidates[:, 0], candidates[:, 1])
        close_indices = indices[distances <= radius_km]

        for idx in close_indices:
            subgraph_nodes.add(node_list[idx])

    print(len(subgraph_nodes))
    subgraph_nodes.update(a_star_path)
    
    return G.subgraph(subgraph_nodes)
