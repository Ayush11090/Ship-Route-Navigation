import networkx as nx
import re
from sklearn.neighbors import BallTree
import numpy as np

def parse_node_id(node_id):
    """Convert node ID string to (lon, lat) tuple"""
    try:
        numbers = re.findall(r"-?\d+\.?\d*", node_id)
        if len(numbers) != 2:
            raise ValueError("Invalid node ID format")
        return (float(numbers[0]), float(numbers[1]))
    except Exception as e:
        print(f"Error parsing node ID {node_id}: {e}")
        return None

def haversine_distance(lat1, lon1, lat2, lon2):
    """Fast haversine approximation in kilometers"""
    R = 6371  # Earth radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def build_spatial_index(G):
    """Create BallTree index for spatial queries using (lat, lon) format"""
    nodes = np.array([(lat, lon) for (lon, lat) in G.nodes()])
    return BallTree(np.radians(nodes), metric='haversine'), nodes

def find_nearest_water_node(G, query_coord, tree):
    """Find nearest graph node to given (lon, lat) coordinate"""
    query = np.radians([[query_coord[1], query_coord[0]]])  # Convert to (lat, lon)
    _, idx = tree.query(query, k=1)
    return list(G.nodes())[idx[0][0]]

def load_navigation_graph(file_path):
    """Load and validate the ship routing graph"""
    G = nx.read_graphml(file_path,node_type=parse_node_id)
    return G

def get_node_coordinates(G, node):
    """Get (lon, lat) coordinates of a node"""
    return (float(G.nodes[node]['lon']), float(G.nodes[node]['lat']))