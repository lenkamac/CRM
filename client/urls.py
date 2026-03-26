from django.urls import path

from client.views import *
from . import views

app_name = 'client'

urlpatterns = [
    path("", ClientListView.as_view(), name="list"),
    path('add/', ClientCreateView.as_view(), name='add'),
    path('<int:pk>/', ClientDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', ClientUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', ClientDeleteView.as_view(), name='delete'),
    path('delete_bulk/', views.clients_bulk_delete, name='delete_bulk'),
    path('<int:pk>/add-comment/', AddCommentView.as_view(), name='add_comment'),
    path('<int:client_id>/edit-comment/<int:comment_id>/', EditCommentView.as_view(), name='edit-client-comment'),
    path('<int:client_id>/comment/<int:comment_id>/delete/', views.delete_client_comment, name='delete_comment'),
    path('<int:pk>/add-file/', AddFileView.as_view(), name='add_client_file'),
    path('export/', views.clients_export, name='export'),
    path('<int:client_id>/file/<int:file_id>/delete/', views.delete_client_file, name='delete_client_file'),
    path('api/exchange-rate/', views.get_exchange_rate, name='exchange_rate'),
    path('<int:pk>/add-purchase/', AddPurchaseView.as_view(), name='add_purchase'),
    path('autocomplete/', views.client_autocomplete, name='autocomplete'),
]
