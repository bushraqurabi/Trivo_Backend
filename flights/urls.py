from django.urls import path
from . import views

urlpatterns = [
   path('main/', views.trivo_main_view),
   path('search/', views.proxy_to_amadeus),
   path ('plan/', views.send_to_gemini),
]

