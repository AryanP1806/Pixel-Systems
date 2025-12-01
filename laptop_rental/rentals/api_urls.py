from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# 1. Create the Router
# This automatically generates URLs for list, detail, add, edit, delete
router = DefaultRouter()

# 2. Register Main Features
router.register(r'products', api_views.ProductAssetViewSet, basename='product')
router.register(r'rentals', api_views.RentalViewSet, basename='rental')
router.register(r'customers', api_views.CustomerViewSet, basename='customer')
# router.register(r'suppliers', api_views.SupplierViewSet, basename='supplier')

# 3. Register the Approval Dashboard
router.register(r'approvals', api_views.ApprovalDashboardViewSet, basename='approval')

# 4. Register Dropdown Options (So the mobile app can populate lists)
router.register(r'options/asset-types', api_views.AssetTypeViewSet, basename='opt-asset-type')
router.register(r'options/cpu', api_views.CPUViewSet, basename='opt-cpu')
router.register(r'options/ram', api_views.RAMViewSet, basename='opt-ram')
router.register(r'options/hdd', api_views.HDDViewSet, basename='opt-hdd')
router.register(r'options/graphics', api_views.GraphicsViewSet, basename='opt-graphics')
router.register(r'options/display', api_views.DisplayViewSet, basename='opt-display')

# 5. Define the URL patterns
urlpatterns = [
    # Include all the router URLs above
    path('', include(router.urls)),
    
    # Custom Login Endpoint
    path('login/', api_views.login_api, name='api_login'),
]