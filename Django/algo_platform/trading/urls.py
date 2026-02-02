from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('', views.dashboard, name='dashboard'), # Default home is dashboard
    path('backtest/', views.backtest_view, name='backtest'),
]