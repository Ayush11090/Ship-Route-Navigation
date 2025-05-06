from shapely.geometry import LineString
from geopy.distance import geodesic

def smooth_path(path, G, tolerance=50):
    """Simplify path using Ramer-Douglas-Peucker algorithm"""
    if len(path) < 3:
        return path
    
    line = LineString([(G.nodes[node]['lon'], G.nodes[node]['lat']) for node in path])
    simplified = line.simplify(tolerance/111000)  # Convert meters to degrees
    
    # Convert back to node sequence
    smoothed_path = []
    for point in simplified.coords:
        nearest_node = min(G.nodes, key=lambda n: geodesic(
            (G.nodes[n]['lat'], G.nodes[n]['lon']),
            (point[1], point[0])
        ).meters)
        smoothed_path.append(nearest_node)
        
    return smoothed_path