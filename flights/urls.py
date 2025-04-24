from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.trivo_main_view, name='trivo_main_view'),
    path('cheapest/', views.proxy_to_amadeus, name='proxy_to_amadeus'),
    path('generate-plan/', views.send_to_gemini, name='send_to_gemini'),
]
