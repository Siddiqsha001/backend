from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel("gemini-2.0-flash")

# Weather API configuration
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

@app.route('/chat', methods=['POST'])
def handle_chat():
    try:
        data = request.json
        message = data.get('message', '').lower()
        city = data.get('city', 'India')  # Default to London if no city provided

        # Check for weather-related keyword
        if 'weather' in message or 'temperature' in message or 'forecast' in message:
            weather_data = get_weather_data(city)

            if 'error' in weather_data:
                # Generate fallback Gemini response without real weather
                prompt = f"""Act like a weather assistant. Since live weather data for {city} isn't available, give a generic weather forecast. 
                Assume mild spring-like weather and include a health tip for such conditions."""
            else:
                # Use real weather data
                prompt = f"""Create a friendly weather report for {city} with this data:
                - Temperature: {weather_data['temp']}°C
                - Conditions: {weather_data['description']}
                - Humidity: {weather_data['humidity']}%
                - Wind: {weather_data['wind_speed']} km/h
                
                Include a short 1-2 sentence health tip based on these conditions."""

            response = model.generate_content(prompt)

            return jsonify({
                "response": response.text,
                "weather_data": None if 'error' in weather_data else weather_data
            })

        # Handle normal chat
        prompt = f"""You are a weather assistant. The user said: '{message}'. 
        Give a helpful, weather-themed reply even if it's not directly a weather question."""
        
        response = model.generate_content(prompt)
        return jsonify({
            "response": response.text,
            "weather_data": None
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "response": "Sorry, I encountered an error processing your request."
        }), 500

def get_weather_data(city):
    try:
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        response = requests.get(WEATHER_API_URL, params=params)
        data = response.json()

        if response.status_code != 200:
            return {'error': data.get('message', 'Unknown weather API error')}

        return {
            'city': data['name'],
            'temp': data['main']['temp'],
            'description': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'icon': data['weather'][0]['icon']
        }
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    app.run(port=5000, debug=True)