from django.contrib import admin
from .models import AdoptablePet, AdoptionRequest

admin.site.register(AdoptablePet)
admin.site.register(AdoptionRequest)
