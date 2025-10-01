from django import forms
from .models import AdoptionRequest

class AdoptionRequestForm(forms.ModelForm):
    class Meta:
        model = AdoptionRequest
        fields = ['message']
