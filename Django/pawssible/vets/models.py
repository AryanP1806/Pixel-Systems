from django.db import models

class Vet(models.Model):
    name = models.CharField(max_length=100)
    qualification = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    years_of_experience = models.PositiveIntegerField()
    clinic_location = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    profile_image = models.ImageField(upload_to='vet_profiles/', blank=True, null=True)


    def __str__(self):
        return f"{self.name} ({self.specialization})"
