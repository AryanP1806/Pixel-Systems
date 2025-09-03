from django.urls import path
from . import views

app_name = 'adoption'

urlpatterns = [
    path('', views.available_pets, name='list'),
    path('adopt/<int:pet_id>/', views.adopt_pet, name='adopt'),
]
