from django.urls import path
from . import views

app_name = 'Staff'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # POS system
    path('pos/', views.pos, name='pos'),
    path('pos/create-sale/', views.create_sale, name='create_sale'),
    path('pos/add-item/', views.add_sale_item, name='add_sale_item'),
    path('pos/remove-item/<int:pk>/', views.remove_sale_item, name='remove_sale_item'),
    path('pos/complete-sale/<int:pk>/', views.complete_sale, name='complete_sale'),

    # Inventory viewing
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/<int:pk>/', views.inventory_detail, name='inventory_detail'),

    # Products viewing
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),

    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),

    # Sales history
    path('sales/', views.sale_history, name='sale_history'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
]