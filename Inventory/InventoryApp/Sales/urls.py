from django.urls import path
from . import views

app_name = 'Sales'

urlpatterns = [
    path('api/products/', views.product_search, name='product_search'),
    path('api/process-sale/', views.process_sale, name='process_sale'),
    path('api/get-sale/<int:pk>/', views.get_sale, name='get_sale'),
    path('api/create-customer/', views.create_customer, name='create_customer'),
]
