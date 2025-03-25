from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.flight_service import get_flights

class FlightSearchView(APIView):
    def get(self, request):
        origin = request.query_params.get('origin')
        destination = request.query_params.get('destination')
        departure_date = request.query_params.get('departure_date')
        return_date = request.query_params.get('return_date', None)

        flights = get_flights(origin, destination, departure_date, return_date)
        
        if "error" in flights:
            return Response({"message": flights["error"]}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"flights": flights}, status=status.HTTP_200_OK)
