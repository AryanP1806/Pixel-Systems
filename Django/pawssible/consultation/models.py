from django.db import models
from django.conf import settings


# Create your models here.
class Consultation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vet_name = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)
    message = models.TextField()
    date_requested = models.DateTimeField(auto_now_add=True)
    video_link = models.URLField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.topic}"
