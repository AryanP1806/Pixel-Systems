from django.db import models
from django.conf import settings

class Appointment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pet_name = models.CharField(max_length=100)
    vet_name = models.CharField(max_length=100)
    date = models.DateField()
    time = models.TimeField()
    symptoms = models.TextField()

    def __str__(self):
        return f"{self.pet_name} with {self.vet_name} on {self.date}"

# Create your models here.
