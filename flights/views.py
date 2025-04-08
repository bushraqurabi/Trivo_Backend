import json
import google.generativeai as genai
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from amadeus import Client, ResponseError
from .models import Flight
from django.conf import settings

# Initialize Amadeus client
amadeus = Client(
    client_id=settings.AMADEUS_CLIENT_ID,
    client_secret=settings.AMADEUS_CLIENT_SECRET
)

# Initialize Gemini AI (Ensure you have Gemini API key and setup)
genai.configure(api_key=settings.GEMINI_API_KEY)

# Combined view for both flight search and plan generation
@csrf_exempt
@api_view(['POST'])
def search_and_generate_plan(request):
    try:
        # 1. Get user input data (origin, destination, etc.) from POST body
        user_data = json.loads(request.body)

        origin = user_data.get('origin', 'NYC')
        destination = user_data.get('destination', 'LAX')
        departure_date = user_data.get('departure_date', '2024-06-01')
        adults = int(user_data.get('adults', 1))

        # 2. Make the request to Amadeus API to search for flights
        flight_response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults
        )

        # 3. Save the flight details in the database
        for offer in flight_response.data:
            Flight.objects.create(
                origin=origin,
                destination=destination,
                departure_time=datetime.fromisoformat(offer['itineraries'][0]['segments'][0]['departure']['at']),
                arrival_time=datetime.fromisoformat(offer['itineraries'][0]['segments'][0]['arrival']['at']),
                price=offer['price']['total']
            )

        # 4. Prepare flight data (or the relevant info) to send to the Gemini AI API for the travel plan
        flight_info = {
            "flights": flight_response.data,
        }

        # Generate travel plan with Gemini API
        prompt = f"Generate a travel plan for flights from {origin} to {destination} on {departure_date}."
        # Adding details from flight info into the prompt
        for flight in flight_info['flights']:
            prompt += f"\nFlight: {flight['itineraries'][0]['segments'][0]['departure']['at']} - {flight['itineraries'][0]['segments'][0]['arrival']['at']} | Price: {flight['price']['total']}"

        # Request the Gemini API to generate a travel plan
        response = genai.generate_text(prompt=prompt)
        travel_plan = response['text']

        # 5. Return the response with flight offers and the generated travel plan
        return JsonResponse({
            'flight_info': flight_info,
            'travel_plan': travel_plan
        })

    except ResponseError as error:
        # Handle errors related to Amadeus API
        return JsonResponse({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        # Handle general exceptions
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
