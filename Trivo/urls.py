from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to Trivo Backend!")  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('flights/', include('flights.urls')),
    path('', home),  
]
