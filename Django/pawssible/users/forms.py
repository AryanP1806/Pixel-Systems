from django import forms
from .models import Profile

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import PetSchedule
from django.contrib.auth import get_user_model

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['pet_name', 'pet_breed', 'pet_age', 'profile_image']


User = get_user_model()

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']



class PetScheduleForm(forms.ModelForm):
    class Meta:
        model = PetSchedule
        fields = ['title', 'description', 'scheduled_time']
        widgets = {
            'scheduled_time': forms.TimeInput(attrs={'type': 'time'}),
            }
