import json
import ssl
from datetime import datetime
from urllib.request import urlopen
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from amadeus import Client, Location, ResponseError
import google.generativeai as genai

# === Initialize Amadeus Client ===
amadeus = Client(
    client_id=settings.AMADEUS_API_KEY,
    client_secret=settings.AMADEUS_API_SECRET,
)


# === 1️⃣ Main View: Orchestrates Flight Search + AI Travel Plan ===
@csrf_exempt
def trivo_main_view(request):
    if request.method == "POST":
        user_data = json.loads(request.body)

        # Step 1: Query the internal cheapest flight search API
        response_1 = requests.post("http://localhost:8000/flights/search/", json=user_data)
        flight_results = response_1.json()
        print("✅ Step 1 - Cheapest Flights Found:", flight_results)

        if "error" in flight_results:
            return JsonResponse(flight_results, status=400)

        # Step 2: Pass flight data to Gemini AI for personalized plan
        response_2 = requests.post("http://localhost:8000/flights/plan/", json={
            "origin": user_data.get("origin"),
            "destination": user_data.get("destination"),
            "departure_date": user_data.get("departure_date"),
            "preferences": user_data.get("preferences", {}),
            "flights": flight_results.get("flights", [])
        })

        ai_plan = response_2.json()
        print("✅ Step 2 - AI Travel Plan Generated:", ai_plan)

        return JsonResponse(ai_plan)

    return JsonResponse({"error": "Only POST method allowed."}, status=405)


# === 2️⃣ Sub-View: Cheapest Flight Search (Amadeus) ===
@csrf_exempt
def proxy_to_amadeus(request):
    if request.method == "POST":
        data = json.loads(request.body)
        origin = data.get("origin")
        destination = data.get("destination")
        departure_date = data.get("departure_date")
        adults = data.get("adults", 1)

        if not all([origin, destination, departure_date]):
            return JsonResponse({"error": "origin, destination, and departure_date are required."}, status=400)

        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                adults=adults
            )

            if not response.data:
                return JsonResponse({"error": "No flights found."}, status=404)

            sorted_flights = sorted(response.data, key=lambda x: float(x['price']['total']))

            cheapest = []
            for offer in sorted_flights:
                segment = offer['itineraries'][0]['segments'][0]
                cheapest.append({
                    "price": offer['price']['total'],
                    "origin": segment['departure']['iataCode'],
                    "destination": segment['arrival']['iataCode'],
                    "departure": segment['departure']['at'],
                    "arrival": segment['arrival']['at'],
                    "carrier": segment['carrierCode']
                })

            return JsonResponse({"flights": cheapest})

        except ResponseError as e:
            return JsonResponse({"error": f"Amadeus API error: {str(e)}"}, status=500)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Only POST method allowed."}, status=405)


# === 3️⃣ Sub-View: AI Travel Plan via Gemini ===
@csrf_exempt
def send_to_gemini(request):
    if request.method == "POST":
        data = json.loads(request.body)
        origin = data.get("origin")
        destination = data.get("destination")
        preferences = data.get("preferences")
        flights = data.get("flights", [])

        if not flights:
            return JsonResponse({"error": "No flight data provided."}, status=400)

        try:
            # Build the AI prompt
            prompt = f"""
            A user wants to fly from {origin} to {destination}.
            Here are the available flights: {json.dumps(flights, indent=2)}
            User preferences: {json.dumps(preferences, indent=2)}
            Please generate a smart, budget-friendly and personalized travel plan.
            """

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-pro")  # Update based on your plan
            result = model.generate_content(prompt)

            return JsonResponse({
                "ai_travel_plan": result.text
            })

        except Exception as e:
            return JsonResponse({"error": f"AI model error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Only POST method allowed."}, status=405)
