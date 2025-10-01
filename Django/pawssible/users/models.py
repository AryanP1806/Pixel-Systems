from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pet_name = models.CharField(max_length=100, blank=True)
    pet_breed = models.CharField(max_length=100, blank=True)
    pet_age = models.IntegerField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', default='default.jpg')
    bio = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
        
    def __str__(self):
        return f"{self.user.username} Profile"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # Prevent crash if profile doesn't exist yet
        Profile.objects.create(user=instance)



class CustomUser(AbstractUser):
    # Add custom fields if needed
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def __str__(self):
        return self.username




class PetSchedule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    scheduled_time = models.TimeField()  # changed to time only
    notified_today = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} at {self.scheduled_time}"