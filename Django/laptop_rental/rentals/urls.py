from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.add_customer, name='add_customer'),
    path('rentals/', views.rental_list, name='rental_list'),
    path('rentals/add/', views.add_rental, name='add_rental'),
    path('history/', views.rental_history, name='rental_history'),
    path('customers/edit/<int:pk>/', views.edit_customer, name='edit_customer')
]
