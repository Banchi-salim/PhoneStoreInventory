from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('api/products/', views.product_list_api, name='product_list_api'),
    path('api/products/<int:pk>/', views.product_detail_api, name='product_detail_api'),
    path('api/inventory/', views.inventory_list_api, name='inventory_list_api'),
    path('api/inventory/<int:pk>/', views.inventory_detail_api, name='inventory_detail_api'),
    path('api/check-barcode/<str:barcode>/', views.check_barcode, name='check_barcode'),
]