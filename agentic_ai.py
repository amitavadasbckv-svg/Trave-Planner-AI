import json
import requests
from langchain_core.tools import tool
from datetime import datetime
from collections import defaultdict,deque
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"  # matches "14:30", "09:15" etc.

@tool
def flight_search(source: str, destination: str):
    """Find direct or alternative flight routes"""

    with open("flights.json") as f:
        flights = json.load(f)

    # -----------------------------
    # 1. Try direct flights first
    # -----------------------------
    direct = [
        f for f in flights
        if f["from"].lower() == source.lower()
        and f["to"].lower() == destination.lower()
    ]

    if direct:
        cheapest = min(direct, key=lambda x: x["price"])

        def duration(f):
            dep = datetime.strptime(f["departure_time"], TIME_FORMAT)
            arr = datetime.strptime(f["arrival_time"], TIME_FORMAT)
            return (arr - dep).total_seconds()

        fastest = min(direct, key=duration)

        return {
            "type": "direct",
            "cheapest": cheapest,
            "fastest": fastest
        }

    # -----------------------------
    # 2. Build graph
    # -----------------------------
    graph = defaultdict(list)
    for f in flights:
        graph[f["from"]].append(f)

    # -----------------------------
    # 3. BFS for alternative routes
    # -----------------------------
    routes = []
    queue = deque()
    queue.append((source, [], {source}))

    MAX_STOPS = 4

    while queue:
        current_city, path, visited = queue.popleft()

        if len(path) > MAX_STOPS:
            continue

        for flight in graph.get(current_city, []):
            next_city = flight["to"]

            if next_city in visited:
                continue

            new_path = path + [flight]

            if next_city == destination:
                routes.append(new_path)
            else:
                queue.append(
                    (next_city, new_path, visited | {next_city})
                )

    if not routes:
        return {
            "type": "none",
            "message": f"No route available from {source} to {destination}"
        }

    # -----------------------------
    # 4. Pick cheapest alternative
    # -----------------------------
    def route_price(route):
        return sum(f["price"] for f in route)

    best = min(routes, key=route_price)

    return {
        "type": "connecting",
        "stops": len(best) - 1,
        "total_price": route_price(best),
        "route": [
            {
                "from": f["from"],
                "to": f["to"],
                "airline": f["airline"],
                "price": f["price"]
            }
            for f in best
        ]
    }

@tool
def hotel_recommendation(city: str, price_per_night: int):
    """Recommend best-rated hotel within budget"""
    with open("hotels.json") as f:
        hotels = json.load(f)

    filtered = [
        h for h in hotels
        if h["city"].lower() == city.lower()
        and h["price_per_night"] <= price_per_night
    ]

    best = max(filtered, key=lambda x: x["stars"])
    return best


@tool
def places_discovery(city: str, place_type: str = "any"):
    """Discover attractions in a city"""
    with open("places.json") as f:
        places = json.load(f)

    results = [
        p for p in places
        if p["city"].lower() == city.lower()
        and (place_type == "any" or p["type"] == place_type)
    ]

    return sorted(results, key=lambda x: x["rating"], reverse=True)


@tool
def weather_lookup(latitude: float, longitude: float):
    """Get 7-day weather forecast"""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    )
    return requests.get(url).json()["daily"]


@tool
def budget_estimation(flight_cost: int, hotel_cost: int, days: int):
    """Estimate total trip cost"""
    local_expense_per_day = 1500
    return {
        "flight": flight_cost,
        "hotel": hotel_cost,
        "local": local_expense_per_day * days,
        "total": flight_cost + hotel_cost + (local_expense_per_day * days)
    }
