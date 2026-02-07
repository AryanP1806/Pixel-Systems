from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('', views.dashboard, name='dashboard'), # Default home is dashboard
    path('backtest/', views.backtest_view, name='backtest'),

    # Strategy Management
    # path('strategy/', views.strategy_list, name='strategy'),

    path('strategies/', views.strategy_list, name='strategy_list'),
    path('strategies/create/', views.strategy_upsert, name='strategy_create'),
    path('strategies/edit/<int:pk>/', views.strategy_upsert, name='strategy_edit'),
    path('strategies/<int:pk>/', views.strategy_viewer, name='strategy_viewer'),
]