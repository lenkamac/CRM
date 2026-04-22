from django.urls import path
from product.views import *
from . import views

app_name = 'product'

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('add/', views.add_product, name='add_product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('autocomplete/', views.product_autocomplete, name='autocomplete'),
    path('sales/', views.SalesListView.as_view(), name='sales_list'),
]