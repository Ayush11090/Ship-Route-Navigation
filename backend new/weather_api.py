import requests
import requests_cache
from retry_requests import retry
import logging
import openmeteo_requests
import json
from datetime import datetime

def datetime_serializer(obj):
    """Custom serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# Configure caching (stores responses for 1 hour)
cache_session = requests_cache.CachedSession('.weather_cache', expire_after=3600)
retry_session = retry(cache_session, retries=3, backoff_factor=0.5)
openmeteo = openmeteo_requests.Client(session = retry_session)

def fetch_weather_data(lat,lon):
    """Fetch and return current weather data in JSON format"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
	    "longitude": lon,
        "current": ["weather_code", "wind_speed_10m", "wind_direction_10m"],
        "forecast_days": 1
    }
    
    try:
        responses = openmeteo.weather_api(url, params=params)
        weather_data_list = []

        for response in responses:
            current = response.Current()
            weather_data = {
                "current": {
                    "weather_code": current.Variables(0).Value(),
                    "wind_speed_10m": current.Variables(1).Value(),
                    "wind_direction_10m": current.Variables(2).Value()
                }
            }
            weather_data_list.append(weather_data)
        # print(weather_data_list[0])
        
        return weather_data_list

    except Exception as e:
        print("Weather API error:", str(e))
        # Return default fallback data for all locations
        return [{
            "current": {
                "weather_code": 1,
                "wind_speed_10m": 10.0,
                "wind_direction_10m": 180
            }
        } for _ in lat]

def fetch_weather_marine_data(lat,lon):
    """
    Fetch marine weather data from Marine Open-Meteo API.
    Returns dictionary with marine data or empty dict on failure.
    """
    
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["wave_height", "wave_direction", "ocean_current_velocity", "ocean_current_direction"]
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        marine_data_list = []

        for response in responses:
            current = response.Current()
            marine_data = {
                "current": {
                    "wave_height": current.Variables(0).Value(),
                    "wave_direction": current.Variables(1).Value(),
                    "ocean_current_velocity": current.Variables(2).Value(),
                    "ocean_current_direction": current.Variables(3).Value()
                }
            }
            marine_data_list.append(marine_data)

        return marine_data_list

    except Exception as e:
        print("Marine API error:", str(e))
        # Return fallback default values
        return [{
            "current": {
                "wave_height": 1.0,
                "wave_direction": 180,
                "ocean_current_velocity": 2.0,
                "ocean_current_direction": 180
            }
        } for _ in lat]
