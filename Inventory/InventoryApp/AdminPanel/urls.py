from django.urls import path
from . import views

app_name = 'AdminPanel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.inventory_add, name='inventory_add'),
    path('inventory/<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('inventory/<int:pk>/edit/', views.inventory_edit, name='inventory_edit'),
    path('inventory/<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),

    # Phones management
    path('phones/', views.phone_list, name='phone_list'),
    path('phones/add/', views.phone_add, name='phone_add'),
    path('phones/<int:pk>/', views.phone_detail, name='phone_detail'),
    path('phones/<int:pk>/edit/', views.phone_edit, name='phone_edit'),
    path('phones/<int:pk>/delete/', views.phone_delete, name='phone_delete'),

    # Accessories management
    path('accessories/', views.accessory_list, name='accessory_list'),
    path('accessories/add/', views.accessory_add, name='accessory_add'),
    path('accessories/<int:pk>/', views.accessory_detail, name='accessory_detail'),
    path('accessories/<int:pk>/edit/', views.accessory_edit, name='accessory_edit'),
    path('accessories/<int:pk>/delete/', views.accessory_delete, name='accessory_delete'),

    # Categories management
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Brands management
    path('brands/', views.brand_list, name='brand_list'),
    path('brands/add/', views.brand_add, name='brand_add'),
    path('brands/<int:pk>/edit/', views.brand_edit, name='brand_edit'),
    path('brands/<int:pk>/delete/', views.brand_delete, name='brand_delete'),

    # Suppliers management
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),

    # Purchases management
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/add/', views.purchase_add, name='purchase_add'),
    path('purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('purchases/<int:pk>/edit/', views.purchase_edit, name='purchase_edit'),
    path('purchases/<int:pk>/delete/', views.purchase_delete, name='purchase_delete'),
    path('purchases/<int:pk>/receive/', views.receive_purchase, name='receive_purchase'),

    # Sales management
    path('sales/', views.sales_list, name='sales_list'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),

    # Staff management
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_add, name='staff_add'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/delete/', views.staff_delete, name='staff_delete'),

    # Branches management
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/add/', views.branch_add, name='branch_add'),
    path('branches/<int:pk>/', views.branch_detail, name='branch_detail'),
    path('branches/<int:pk>/edit/', views.branch_edit, name='branch_edit'),
    path('branches/<int:pk>/delete/', views.branch_delete, name='branch_delete'),

    # Reports
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
    path('reports/purchases/', views.purchases_report, name='purchases_report'),
    path('reports/profit/', views.profit_report, name='profit_report'),
    path('reports/export/<int:pk>/', views.export_report, name='export_report'),

    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),

    # reports
    path('generate/sales/', views.generate_sales_report, name='generate_sales_report'),
    path('generate/inventory/', views.generate_inventory_report, name='generate_inventory_report'),
    path('generate/purchases/', views.generate_purchases_report, name='generate_purchases_report'),
    path('generate/profit/', views.generate_profit_report, name='generate_profit_report'),
    path('download/<int:pk>/', views.download_report, name='download_report'),
]