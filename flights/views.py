import json
from datetime import datetime
import requests

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework import status

from amadeus import Client, ResponseError
from django.conf import settings

import google.generativeai as genai
from .models import Flight

# === Initialize Amadeus Client ===
amadeus = Client(
    client_id=settings.AMADEUS_API_KEY,
    client_secret=settings.AMADEUS_API_SECRET
)

# === Initialize Gemini AI ===
genai.configure(api_key=settings.GEMINI_API_KEY)


# === 1️⃣ Combined View: Search Flights + Generate Plan ===
@csrf_exempt
@api_view(['POST'])
def trivo_main_view(request):
    try:
        user_data = request.data
        
        # Ensure the required fields are present
        origin = user_data.get('origin')
        destination = user_data.get('destination')
        departure_date = user_data.get('departure_date')
        adults = user_data.get('adults')

        if not all([origin, destination, departure_date, adults]):
            return JsonResponse({'error': 'Missing required fields: origin, destination, departure_date, and adults.'}, status=400)

        try:
            adults = int(adults)  # Ensure 'adults' is an integer
        except ValueError:
            return JsonResponse({'error': 'Invalid value for adults. It should be an integer.'}, status=400)

        # 2. Query Amadeus for flights
        flight_response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults
        )

        # 3. Save flights to DB
        for offer in flight_response.data:
            Flight.objects.create(
                origin=origin,
                destination=destination,
                departure_time=datetime.fromisoformat(offer['itineraries'][0]['segments'][0]['departure']['at']),
                arrival_time=datetime.fromisoformat(offer['itineraries'][0]['segments'][0]['arrival']['at']),
                price=offer['price']['total']
            )

        # 4. Build AI prompt
        prompt = f"Generate a travel plan for flights from {origin} to {destination} on {departure_date}."
        for flight in flight_response.data:
            prompt += f"\nFlight: {flight['itineraries'][0]['segments'][0]['departure']['at']} - {flight['itineraries'][0]['segments'][0]['arrival']['at']} | Price: {flight['price']['total']}"

        # 5. Call Gemini AI
        model = genai.GenerativeModel("gemini-1.5-pro")
        result = model.generate_content(prompt)

        return JsonResponse({
            'flight_info': flight_response.data,
            'travel_plan': result.text
        })

    except ResponseError as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# === 2️⃣ Sub-View: Cheapest Flights Search ===
@csrf_exempt
def proxy_to_amadeus(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Extract parameters from request
            origin = data.get("origin")
            destination = data.get("destination")
            departure_date = data.get("departure_date")
            adults = int(data.get("adults", 1))

            # Validate required fields
            if not all([origin, destination, departure_date]):
                return JsonResponse({"error": "origin, destination, and departure_date are required."}, status=400)

            # Query Amadeus for flight offers
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                adults=adults
            )

            # Check if no flights are found
            if not response.data:
                return JsonResponse({"error": "No flights found."}, status=404)

            # Sort flights by price
            sorted_flights = sorted(response.data, key=lambda x: float(x['price']['total']))

            # Format the flight details to return
            cheapest_flights = [{
                "price": offer['price']['total'],
                "origin": offer['itineraries'][0]['segments'][0]['departure']['iataCode'],
                "destination": offer['itineraries'][0]['segments'][0]['arrival']['iataCode'],
                "departure": offer['itineraries'][0]['segments'][0]['departure']['at'],
                "arrival": offer['itineraries'][0]['segments'][0]['arrival']['at'],
                "carrier": offer['itineraries'][0]['segments'][0]['carrierCode']
            } for offer in sorted_flights]

            return JsonResponse({"flights": cheapest_flights})

        except ResponseError as e:
            return JsonResponse({"error": f"Amadeus API error: {str(e)}"}, status=500)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Only POST method allowed."}, status=405)


# === 3️⃣ Sub-View: Generate AI Travel Plan from Flight Data ===
@csrf_exempt
def send_to_gemini(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Extract parameters from the request
            origin = data.get("origin")
            destination = data.get("destination")
            preferences = data.get("preferences", {})
            flights = data.get("flights", [])

            # Check if flight data is provided
            if not flights:
                return JsonResponse({"error": "No flight data provided."}, status=400)

            # Construct the prompt for the Gemini model
            prompt = f"""
            A user wants to fly from {origin} to {destination}.
            Here are the available flights: {json.dumps(flights, indent=2)}
            User preferences: {json.dumps(preferences, indent=2)}
            Please generate a smart, budget-friendly, and personalized travel plan.
            """

            # Call Gemini AI to generate the travel plan
            model = genai.GenerativeModel("gemini-1.5-pro")
            result = model.generate_content(prompt)

            return JsonResponse({"ai_travel_plan": result.text})

        except Exception as e:
            return JsonResponse({"error": f"AI model error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Only POST method allowed."}, status=405)