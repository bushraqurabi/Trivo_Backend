from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from flights.utils import amadeus
from amadeus import ResponseError

@api_view(['GET'])
def search_flights(request):
    try:
        origin = request.GET.get('origin')
        destination = request.GET.get('destination')
        departure_date = request.GET.get('departure_date')
        adults = request.GET.get('adults', 1)

        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults
        )
        return Response(response.data)
    except ResponseError as error:
        return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)