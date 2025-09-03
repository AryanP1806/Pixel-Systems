from django.db import models
from django.conf import settings

# Create your models here.
class AdoptablePet(models.Model):
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    age = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='adoption_pets/')
    location = models.CharField(max_length=200)
    available = models.BooleanField(default=True)
    # type = models.CharField(max_length=20, choices=[('dog', 'Dog'), ('cat', 'Cat')])
    # posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # is_adopted = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.name} ({self.breed})"

class AdoptionRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pet = models.ForeignKey(AdoptablePet, on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=[('Pending','Pending'),('Approved','Approved'),('Rejected','Rejected')], default='Pending')

    def __str__(self):
        return f"{self.user.username} - {self.pet.name}"
