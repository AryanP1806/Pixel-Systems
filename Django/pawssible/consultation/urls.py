from django.urls import path
from . import views

app_name = 'consultation'

urlpatterns = [
    path('request/', views.request_consultation, name='request'),
    path('success/', views.consultation_success, name='success'),
]
