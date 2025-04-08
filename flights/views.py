import json
from datetime import datetime
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Flight
from .amadeus_client import amadeus
from amadeus import ResponseError


@api_view(["GET"])
def search_flights(request):
    try:
        origin = request.GET.get("origin", "NYC")
        destination = request.GET.get("destination", "LAX")
        departure_date = request.GET.get("departure_date", "2024-06-01")
        adults = int(request.GET.get("adults", 1))

        # Call Amadeus API
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults,
        )

        for offer in response.data:
            Flight.objects.create(
                origin=origin,
                destination=destination,
                departure_time=datetime.fromisoformat(
                    offer["itineraries"][0]["segments"][0]["departure"]["at"]
                ),
                arrival_time=datetime.fromisoformat(
                    offer["itineraries"][0]["segments"][0]["arrival"]["at"]
                ),
                price=offer["price"]["total"],
            )

        return Response(response.data)

    except ResponseError as error:
        print("Amadeus API Error:", error)
        print("Details:", error.response.body)
        return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
