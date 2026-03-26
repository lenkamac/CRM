from django.urls import path
from .views import *
from . import views


app_name = 'lead'

urlpatterns = [
    path("", LeadListView.as_view(), name="list"),
    path('add/', LeadCreateView.as_view(), name='add'),
    path('<int:pk>/', LeadDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', LeadUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', LeadDeleteView.as_view(), name='delete'),
    path('delete_bulk/', views.leads_bulk_delete, name='delete_bulk'),
    path('<int:pk>/add-comment/', AddCommentView.as_view(), name='add_comment'),
    path('<int:lead_id>/edit-comment/<int:comment_id>/', EditCommentView.as_view(), name='edit-comment'),
    path('<int:lead_id>/comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('<int:pk>/add-file/', AddFileView.as_view(), name='add_file'),
    path('export/', views.leads_export, name='export'),
    path('convert-lead/<int:lead_id>/', convert_lead_to_client, name='convert_lead'),
    path('<int:lead_id>/file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('autocomplete/', views.lead_autocomplete, name='autocomplete'),
]