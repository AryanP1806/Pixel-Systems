from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.view_profile, name='profile'),
    path('profile/', views.view_profile, name='profile'),
    path('edit/', views.edit_profile, name='edit'),
    path('register/', views.register, name='register'),
    path('schedule/', views.user_schedule, name='schedule'),
    path('schedule/create/', views.create_schedule, name='create_schedule'),
    path('schedule/list/', views.schedule_list, name='schedule_list'),
    path('schedule/api/', views.upcoming_schedules_api, name='schedule_api'),
]
