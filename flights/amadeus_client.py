import ssl
from urllib.request import urlopen
from amadeus import Client
from django.conf import settings

def ssl_disabled_urlopen(endpoint):
    context = ssl._create_unverified_context()
    return urlopen(endpoint, context=context)

amadeus = Client(
    client_id=settings.AMADEUS_API_KEY,
    client_secret=settings.AMADEUS_API_SECRET,
    http=ssl_disabled_urlopen
)
