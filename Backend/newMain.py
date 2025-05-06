import sys
import networkx as nx
from geopy.distance import geodesic  # Import geodesic function
from smooth import bspline_smooth
from tqdm import tqdm
import asyncio
import websockets
import json
import time
import numpy as np
from collections import defaultdict
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from cost_calculation import combined_cost, calculate_weather_cost
from weather_api import fetch_weather_data, fetch_weather_marine_data
from graph_loader import load_navigation_graph, build_spatial_index, find_nearest_water_node
from build_subgraph import build_subgraph
from plot import plot_subgraph

weather_data = {}
marine_data = {}

# Radius of Earth in nautical miles
R_NM = 3440.065

def haversine_distance(coord1, coord2):
    """Calculate the Haversine distance in nautical miles between two (lon, lat) coordinates."""
    lon1, lat1 = coord1
    lon2, lat2 = coord2

    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R_NM * c

def calculate_total_nautical_distance(path):
    """Calculate the total distance along the path (list of coordinates) in nautical miles."""
    total_distance = 0
    for i in range(len(path) - 1):
        dist = haversine_distance(path[i], path[i + 1])
        total_distance += dist
    return total_distance

class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def wait(self):
        """Block until we can make another API call"""
        now = time.time()
        # Remove expired calls
        self.calls = [t for t in self.calls if now - t < self.period]
        
        if len(self.calls) >= self.max_calls:
            oldest = self.calls[0]
            sleep_time = self.period - (now - oldest)
            if sleep_time > 0:
                print(f"Rate limit reached. Sleeping {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
            self.calls = []
        self.calls.append(time.time())

def _calculate_geographic_bearing(pointA, pointB):
    lat1, lon1 = np.radians(pointA[1]), np.radians(pointA[0])
    lat2, lon2 = np.radians(pointB[1]), np.radians(pointB[0])

    dLon = lon2 - lon1
    x = np.sin(dLon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dLon)
    initial_bearing = np.arctan2(x, y)
    return (np.degrees(initial_bearing) + 360) % 360

def batch_fetch_weather_data(locations, batch_size=100):
    """Fetch weather and marine data in batches with rate limiting"""
    weather_results = {}
    marine_results = {}

    batch_count = 0
    minute_start_time = None

    # Process in batches
    for i in range(0, len(locations), batch_size):
        if batch_count % 5 == 0:
            minute_start_time = time.time()

        batch = locations[i:i+batch_size]
        lats = [loc[0] for loc in batch]
        lons = [loc[1] for loc in batch]

        # Fetch weather data
        weather_data = fetch_weather_data(lats, lons)

        # Fetch marine data
        marine_data = fetch_weather_marine_data(lats, lons)

        # Store results with location as key
        for j, loc in enumerate(batch):
            weather_results[loc] = weather_data[j] if j < len(weather_data) else {}
            marine_results[loc] = marine_data[j] if j < len(marine_data) else {}

        batch_count += 1
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processed batch {batch_count}/{(len(locations) + batch_size - 1) // batch_size}")

        time.sleep(11)

    return weather_results, marine_results

def update_subgraph_weights(subgraph, start_node, end_node):
    """Update edge weights with weather-aware costs using target node's weather data"""
    # Calculate total distance for normalization
    try:
        total_distance = nx.shortest_path_length(subgraph, start_node, end_node, weight='distance')
    except nx.NetworkXNoPath:
        total_distance = float('inf')
    
    # Precompute remaining distances from each node to destination
    remaining_distances = {}
    for node in subgraph.nodes():
        try:
            remaining_distances[node] = nx.shortest_path_length(subgraph, node, end_node, weight='distance')
        except nx.NetworkXNoPath:
            remaining_distances[node] = float('inf')

    # Collect all unique target node locations and bearings for each edge
    edge_locations = {}
    bearings = {}
    
    for u, v, data in subgraph.edges(data=True):
        # Target node's coordinates (lat, lon)
        target_lat = v[1]
        target_lon = v[0]
        edge_locations[(u, v)] = (target_lat, target_lon)
        
        # Calculate bearing from u to v using (lat, lon) tuples
        u_lat, u_lon = u[1], u[0]
        v_lat, v_lon = v[1], v[0]
        bearing = _calculate_geographic_bearing((u_lat, u_lon), (v_lat, v_lon))
        bearings[(u, v)] = bearing

    # Batch fetch weather data for all unique target locations
    unique_locations = list(set(edge_locations.values()))
    weather_data, marine_data = batch_fetch_weather_data(unique_locations)
    
    # Create location to edges mapping
    location_to_edges = defaultdict(list)
    for edge, loc in edge_locations.items():
        location_to_edges[loc].append(edge)

    # Update all edges with weather data from their target node's location
    for loc in unique_locations:
        current_weather = weather_data.get(loc, {})
        current_marine = marine_data.get(loc, {})
        edges = location_to_edges[loc]
        for (u, v) in edges:
            try:
                bearing = bearings[(u, v)]
                weather_penalty = calculate_weather_cost(
                    {'weather': current_weather, 'marine': current_marine},
                    bearing
                )
                print(weather_penalty)
                remaining = remaining_distances.get(v, float('inf'))
                data = subgraph[u][v]
                original_weight = data.get('original_weight', data['weight'])
                data['original_weight'] = original_weight  # Preserve original
                cost = combined_cost(
                    original_weight,
                    remaining,
                    weather_penalty,
                    0,  # direction_penalty (if used)
                    total_distance
                )

                import math

                if math.isnan(cost):
                    data['weight'] = 0
                else:
                    data['weight'] = cost
                print(cost)
                

            except Exception as e:
                print(f"Error processing edge ({u}-{v}): {str(e)}")
                # Fallback to original weight on error
                data['weight'] = data.get('original_weight', original_weight)
    return subgraph

async def handle_navigation(websocket):
    try:
        message = await websocket.recv()
        data = json.loads(message)
        print(data)
        start_coords = tuple(data["start"])  # Converts list to tuple (lat, lon)
        end_coords = tuple(data["end"])      # Converts list to tuple (lat, lon)
        # Load graph with node parsing
        G = load_navigation_graph(
            "E:/grid_based_ship_routes/Backend/grid_based_ship_routes.graphml"
        )

        # Input coordinates (Mumbai to Cape Town)
        start = (start_coords[1],start_coords[0])
        end = (end_coords[1],end_coords[0])
        
        # Build spatial index and node array
        tree, node_array = build_spatial_index(G)

        # Get nearest navigable nodes
        start_node = find_nearest_water_node(G, start, tree)
        end_node = find_nearest_water_node(G, end, tree)

        # Calculate optimal path using A*
        a_star_path = nx.astar_path(G, start_node, end_node, weight='weight')

        # Build and plot optimized subgraph
        subgraph = build_subgraph(G, tree, node_array, a_star_path)
        subgraph = subgraph.to_directed()  # Ensure directed graph
        output_path = "subgraph.graphml"
        nx.write_graphml(subgraph, output_path)
        print(f"Subgraph saved to {output_path}")
        # plot_subgraph(subgraph, a_star_path)
        
        # After initial subgraph creation
        print("Updating edge weights with weather data...")
        optimized_subgraph = update_subgraph_weights(subgraph.copy(), start_node, end_node)
        
        # Save optimized subgraph
        nx.write_graphml(optimized_subgraph, "optimized_subgraph.graphml")
        print(f"Optimized Subgraph saved to {output_path}")
    
        # Find optimized path using new weights
        optimized_path = nx.dijkstra_path(optimized_subgraph, start_node, end_node, weight='weight')
        print(optimized_path)

        smooth_path = optimized_path
        # Plot optimized path
        # plot_subgraph(optimized_subgraph, optimized_path)
        
        Weatherpoints = []
        for i in range(len(smooth_path)):
            u = smooth_path[i]
            
            point_a = (u[1], u[0])  # (lat, lon)
            Weatherpoints.append(point_a)

        # Fetch fresh weather data for midpoints
        weather_results, marine_results = batch_fetch_weather_data(Weatherpoints)

        # Build weather info for midpoints
        weather_info_list = []
        for weatherpoint in Weatherpoints:
            current_weather = weather_results.get(weatherpoint, {}).get("current", {})
            current_marine = marine_results.get(weatherpoint, {}).get("current", {})
            
            weather_info = {
                'coordinate': [weatherpoint[0], weatherpoint[1]],
                'wind_speed': current_weather.get('wind_speed_10m', 'N/A'),
                'wind_direction': current_weather.get('wind_direction_10m', 'N/A'),
                'wave_height': current_marine.get('wave_height', 'N/A'),
                'wave_dir': current_marine.get('wave_direction', 'N/A'),
                'current_vel': current_marine.get('ocean_current_velocity', 'N/A'),
                'current_dir' : current_marine.get('ocean_current_direction', 'N/A')
            }
            weather_info_list.append(weather_info)

        print(weather_info_list)
        # Smooth path and prepare response
       
        new_smooth_path = [(node[1], node[0]) for node in smooth_path]
        distance = calculate_total_nautical_distance(new_smooth_path)
        distance = distance*1.852
        round(distance, 3)
        await websocket.send(json.dumps({
            'type': 'final',
            'path': new_smooth_path,
            'weather': weather_info_list,
            'distance': distance
        }))
    except Exception as e:
        await websocket.send(json.dumps({'type': 'error', 'message': str(e)}))
        raise

async def main():
    print("WebSocket server is starting on ws://localhost:5000")
    async with websockets.serve(handle_navigation, "localhost", 5000):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())