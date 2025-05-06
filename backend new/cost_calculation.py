import numpy as np

# Constants for normalization
MAX_WIND_SPEED = 48.0  # km/h (50 m/s)
MAX_WAVE_HEIGHT = 8.0    # meters
MAX_CURRENT_VELOCITY = 10.8  # km/h (3 m/s)
WEATHER_CODE_MAX = 10    # Scale 0-10 for weather severity

# Ideal values
IDEAL_WIND_SPEED = 0.0
IDEAL_WAVE_HEIGHT = 0.0
IDEAL_CURRENT_VELOCITY = 0.0
IDEAL_WEATHER_CODE = 0

def safe_get(data, key, ideal_value):
    """Retrieve a value safely, returning the ideal value if missing or invalid."""
    try:
        value = data[key]
        return float(value) if isinstance(value, (int, float)) else ideal_value
    except (KeyError, TypeError, ValueError):
        return ideal_value

def calculate_weather_cost(weather_data, desired_bearing):
    """
    Calculate weather penalty considering directional alignment
    weather_data: Dictionary containing:
        - wind_speed_10m (km/h)
        - wind_direction_10m (degrees)
        - wave_height (meters)
        - wave_direction (degrees)
        - ocean_current_velocity (km/h)
        - ocean_current_direction (degrees)
        - weather_code (0-10)
    desired_bearing: Target direction in degrees (0-360)
    """
    try:
        # Access current data with proper fallbacks
        current_weather = weather_data.get('weather', {}).get('current', {})
        current_marine = weather_data.get('marine', {}).get('current', {})

        # Retrieve values with safe defaults
        wind_speed = safe_get(current_weather, "wind_speed_10m", IDEAL_WIND_SPEED)
        wind_dir = safe_get(current_weather, "wind_direction_10m", desired_bearing) % 360
        wave_height = safe_get(current_marine, "wave_height", IDEAL_WAVE_HEIGHT)
        wave_dir = safe_get(current_marine, "wave_direction", desired_bearing) % 360
        current_vel = safe_get(current_marine, "ocean_current_velocity", IDEAL_CURRENT_VELOCITY)
        current_dir = safe_get(current_marine, "ocean_current_direction", desired_bearing) % 360

        # Direction alignment calculations
        def alignment_penalty(actual_dir):
            diff = min(abs(actual_dir - desired_bearing), 360 - abs(actual_dir - desired_bearing))
            return (1 - np.cos(np.radians(diff))) / 2  # 0=aligned, 1=opposed

        # Component penalties with safe divisions
        components = {
            'wind': (wind_speed / MAX_WIND_SPEED) * 0.4 + alignment_penalty(wind_dir) * 0.2,
            'wave': (wave_height / MAX_WAVE_HEIGHT) * 0.2 + alignment_penalty(wave_dir) * 0.95,
            'current': (current_vel / MAX_CURRENT_VELOCITY) * 0.1 + alignment_penalty(current_dir) * 0.05
        }

        return sum(components.values())

    except Exception as e:
        print(f"Error calculating weather cost: {e}")
        return 0.5  # Default average penalty

def combined_cost(edge_distance, remaining_distance, weather_penalty, direction_penalty, total_distance):
    """
    Combined cost function with persistent remaining distance impact
    Weights (sum to 1.0):
    - 15% edge distance
    - 30% remaining distance (log-scaled)
    - 40% weather factors
    - 15% directional alignment
    """
    # Handle potential zero distances
    safe_total = max(total_distance, 1e-6)
    safe_remaining = max(remaining_distance, 1e-6)
    
    # Logarithmic scaling factors
    log_total = np.log1p(safe_total)  # log(1 + total)
    log_remaining = np.log1p(safe_remaining)  # log(1 + remaining)
    
    # Dynamic edge normalization
    max_edge = max(100.0, safe_total * 0.05)  # 5% of total or 100km
    
    
    return (
        
        0.5* (log_remaining / log_total) +  # Maintains impact when small
        0.5 * weather_penalty 
    )
