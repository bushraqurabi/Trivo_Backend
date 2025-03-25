from django.urls import path
from .views import FlightSearchView

urlpatterns = [
    path('flight-search/', FlightSearchView.as_view(), name='flight-search'),
]
