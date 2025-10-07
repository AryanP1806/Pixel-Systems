from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('add/', views.add_student, name='add_student'),
    path('view/', views.view_students, name='view_students'),
    path('delete/<str:student_id>/', views.delete_student, name='delete_student'),
]
