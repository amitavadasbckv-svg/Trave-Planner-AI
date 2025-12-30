# app.py
import streamlit as st
from langchain_core.messages import HumanMessage
from agent import agent
from geopy.geocoders import Nominatim
import requests
from datetime import date, timedelta
 

st.set_page_config(page_title="Agentic AI Trip Planner", layout="wide")
st.title("🌴 Trip Planner AI")

# ----------------------
# User Input
# ----------------------
st.sidebar.header("Trip Details")
source = st.sidebar.text_input("Source City", value="Delhi")
destination = st.sidebar.text_input("Destination City", value="Goa")
days = st.sidebar.number_input("Number of Days", min_value=1, max_value=30, value=5)
preferences = st.sidebar.text_area("Preferences", value="I like beaches and historical places.")
hotel_budget = st.sidebar.number_input("Hotel Budget per Night (₹)", min_value=500, max_value=20000, value=4000)
selected_date = st.sidebar.date_input(
    "📅 Select a date",
    value=date.today()
)
end_date = selected_date + timedelta(days=days - 1)

def weather_lookup(latitude: float, longitude: float):
    """Get 7-day weather forecast"""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&daily=temperature_2m_max,temperature_2m_min,weathercode"
        "&timezone=auto"
    )
    return requests.get(url).json()["daily"]

def safe_get(lst, i):
    return lst[i] if i < len(lst) else None

def get_weather_for_next_days(weather_data, start_date, days):
    forecasts = []
    start_date_str = start_date.strftime("%Y-%m-%d")

    for i, day in enumerate(weather_data["time"]):
        if day >= start_date_str and len(forecasts) < days:
            forecasts.append({
                "date": day,
                "min": weather_data["temperature_2m_min"][i],
                "max": weather_data["temperature_2m_max"][i],
                "code": weather_data["weathercode"][i]
            })

    return forecasts




geolocator = Nominatim(user_agent="travel_planner")
destination = destination
location = geolocator.geocode(destination)
lat, lon = location.latitude, location.longitude

weathers = weather_lookup(lat,lon)

weather_results = get_weather_for_next_days(weathers, selected_date, days)

#print(result)

WEATHER_CODE_MAP = {
    0: "Clear sky ☀️",
    1: "Mainly clear 🌤️",
    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",
    45: "Fog 🌫️",
    48: "Depositing rime fog 🌫️",
    51: "Light drizzle 🌦️",
    53: "Moderate drizzle 🌦️",
    55: "Dense drizzle 🌧️",
    61: "Slight rain 🌧️",
    63: "Moderate rain 🌧️",
    65: "Heavy rain 🌧️",
    71: "Snow fall ❄️",
    80: "Rain showers 🌦️",
    95: "Thunderstorm ⛈️"
}


if st.sidebar.button("Plan Trip"):
    # 🔥 STRUCTURED AGENT PROMPT
    query = f"""
    You are a professional travel planner.

    Trip Details:
    - From: {source}
    - To: {destination}
    - Duration: {days} days
    - Travel Dates: {selected_date} to {end_date}
    - Hotel Budget: ₹{hotel_budget} per night

    User Preferences:
    {preferences}

    Create a day-wise itinerary including:
    - Sightseeing
    - Local food suggestions
    - Leisure & rest
    - Travel tips
    """

    st.info("Generating trip plan... ⏳")

    try:
        # Invoke the agent
        result = agent.invoke({
            "messages": [
                HumanMessage(content=query)
            ]
        })

        # Display the latest message from agent
        trip_plan = result["messages"][-1].content
        st.success("Trip plan generated successfully! ✅")
        st.sidebar.markdown(
        f"""
        **📆 Trip Duration**
        - Start: `{selected_date}`
        - End: `{end_date}`
        """
        )
        st.markdown(trip_plan)
        st.subheader("Weather Forecast")
        if weather_results:
            for w in weather_results:
                weather_text = WEATHER_CODE_MAP.get(w["code"], "Unknown weather")
                st.markdown(
                     f"""
                        **📅 {w['date']}**
                        - Condition: {weather_text}
                        - Min Temp: {w['min']} °C
                        - Max Temp: {w['max']} °C
                    """
                )
        else:
            st.warning("❌ Weather forecast not available.")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
