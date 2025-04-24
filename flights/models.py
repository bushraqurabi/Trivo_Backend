from django.db import models

class Flight(models.Model):
    origin = models.CharField(max_length=100)  # Origin of the flight (e.g., NYC)
    destination = models.CharField(max_length=100)  # Destination of the flight (e.g., LON)
    departure_time = models.DateTimeField()  # Date and time of departure
    arrival_time = models.DateTimeField()  # Date and time of arrival
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price of the flight
    
    # Optional: You could enforce a positive price for validation
    def clean(self):
        if self.price <= 0:
            raise ValidationError('Price must be a positive value.')

    def __str__(self):
        return f"{self.origin} to {self.destination}"

    class Meta:
        # Adding indexes can speed up searches
        indexes = [
            models.Index(fields=['origin', 'destination', 'departure_time']),
        ]
