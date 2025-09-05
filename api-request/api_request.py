import requests
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("api_key")

api_url = f"http://api.weatherstack.com/current?access_key={api_key}&query=Ho Chi Minh"
def fetch_data():
    print("Fetching data from WeatherStack...")
    try:    
        response = requests.get(api_url)
        response.raise_for_status()
        print("API Response received successfully.")
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        raise
def fetch_mock_data():
    print("Fetching mock data...")
    mock_data = {
        "location": {
            "name": "New York",
            "country": "United States of America",
            "region": "New York",
            "lat": "40.714",
            "lon": "-74.006",
            "timezone_id": "America/New_York",
            "localtime": "2023-10-01 10:00",
            "localtime_epoch": 1696154400,
            "utc_offset": "-4.0"
        },
        "current": {
            "observation_time": "02:00 PM",
            "temperature": 22,
            "weather_code": 113,
            "weather_icons": [
                "https://assets.weatherstack.com/images/wsymbols01_png_64/wsymbol_0001_sunny.png"
            ],
            "weather_descriptions": [
                "Sunny"
            ],
            "wind_speed": 13,
            "wind_degree": 240,
            "wind_dir": "WSW",
            "pressure": 1012,
            "precip": 0,
            "humidity": 56,
            "cloudcover": 0,
            "feelslike": 24,
            "uv_index": 5,
            "visibility": 16,
            "is_day": "yes"
        }
    }
    return mock_data
        
print(fetch_data())