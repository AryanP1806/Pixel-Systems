from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import path
from .views import AssetAutocomplete, CustomerAutocomplete


urlpatterns = [
    path('', views.homepage, name='home'),

    path('settings/', views.settings_page, name='settings_page'),
    path('settings/', views.settings_home, name='settings_home'),
    path('settings/cpu/', views.manage_cpu_Options, name='manage_cpu_Options'),
    path('settings/hdd/', views.manage_hdd_Options, name='manage_hdd_Options'),
    path('settings/ram/', views.manage_ram_Options, name='manage_ram_Options'),
    path('settings/display/', views.manage_display_size_Options, name='manage_display_size_Options'),
    path('settings/graphics/', views.manage_graphics_Options, name='manage_graphics_Options'),

    path('asset-types/', views.asset_type_list, name='asset_type_list'),
    path('asset-types/add/', views.add_asset_type, name='add_asset_type'),
    path('asset-types/edit/<int:pk>/', views.edit_asset_type, name='edit_asset_type'),


    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:pk>/add_config/', views.add_config, name='add_config'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/clone/<int:pk>/', views.clone_product, name='clone_product'),
    path('products/sold/', views.sold_assets, name='sold_assets'),
    path('products/<int:pk>/repair/', views.add_repair, name='add_repair'),


    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.add_customer, name='add_customer'),
    path('customers/edit/<int:pk>/', views.edit_customer, name='edit_customer'),
    
    path('rentals/', views.rental_list, name='rental_list'),
    path('rentals/add/', views.add_rental, name='add_rental'),
    path('rentals/complete/<int:rental_id>/', views.mark_rental_completed, name='mark_rental_completed'),
    path('rentals/edit/<int:rental_id>/', views.edit_rental, name='edit_rental'),
    # path('rentals/check_overdue/', views.check_overdue_view, name='check_overdue'),
    path('send-billing-reminder/', views.send_billing_reminder, name='send_billing_reminder'),
    path("check-contracts/", views.check_contracts, name="check_contracts"),
    
    path('history/', views.rental_history, name='rental_history'),    

    path('config/edit/<int:config_id>/', views.edit_config, name='edit_config'),
    path('config/delete/<int:config_id>/', views.delete_config, name='delete_config'),
    path('repair/<int:pk>/edit/', views.edit_repair, name='edit_repair'),
    path('repair/<int:pk>/delete/', views.delete_repair, name='delete_repair'),

    # path('products/submit/', views.submit_product, name='submit_product'),
    path('approvals/', views.approval_dashboard, name='approval_dashboard'),
    path('approvals/product/approve/<int:pk>/', views.approve_product, name='approve_product'),
    path('approvals/product/reject/<int:pk>/', views.reject_product, name='reject_product'),
    path('approvals/customer/approve/<int:pk>/', views.approve_customer, name='approve_customer'),
    path('approvals/customer/reject/<int:pk>/', views.reject_customer, name='reject_customer'),
    path('approvals/rental/approve/<int:pk>/', views.approve_rental, name='approve_rental'),
    path('approvals/rental/reject/<int:pk>/', views.reject_rental, name='reject_rental'),
    path('approvals/config/approve/<int:pk>/', views.approve_config, name='approve_config'),
    path('approvals/config/reject/<int:pk>/', views.reject_config, name='reject_config'),
    
    path('approvals/config/edit/approve/<int:pk>/', views.approve_edited_config, name='approve_edited_config'),
    path('approvals/config/edit/reject/<int:pk>/', views.reject_edited_config, name='reject_edited_config'),
    path('approvals/repair/edit/approve/<int:pk>/', views.approve_repair_edit, name='approve_edited_repair'),
    path('approvals/repair/edit/reject/<int:pk>/', views.reject_edited_repair, name='reject_edited_repair'),

    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),
    path('suppliers/edit/<int:pk>/', views.edit_supplier, name='edit_supplier'),
    
    path('reports/', views.report_dashboard, name='report_dashboard'),
    path('reports/', views.report_dashboard, name='report_dashboard'),
    path('reports/export/csv/', views.export_reports_csv, name='export_reports_csv'),
    path('reports/export/excel/', views.export_reports_excel, name='export_reports_excel'),
    path('reports/export/pdf/', views.export_reports_pdf, name='export_reports_pdf'),


    path('customer-autocomplete/', CustomerAutocomplete.as_view(), name='customer-autocomplete'),
    path('asset-autocomplete/', AssetAutocomplete.as_view(), name='asset-autocomplete'),
]
