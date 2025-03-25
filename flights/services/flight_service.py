import os
from amadeus import Client
from dotenv import load_dotenv

load_dotenv()

amadeus = Client(
    client_id=os.getenv("AMADEUS_API_KEY"),
    client_secret=os.getenv("AMADEUS_API_SECRET")
)

def get_flights(origin, destination, departure_date, return_date=None):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            returnDate=return_date
        )
        return response.data
    except Exception as e:
        print(f"Error fetching flights: {e}")
        return {"error": str(e)}
