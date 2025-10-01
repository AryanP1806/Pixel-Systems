# chatbot/urls.py
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('response/', views.chatbot_response, name='chat_response'),
]
