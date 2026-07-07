from django.urls import path
from . import views

app_name = 'opportunity'

urlpatterns = [
    path('', views.OpportunityListView.as_view(), name='list'),
    path('add/', views.OpportunityCreateView.as_view(), name='add'),
    path('<int:pk>/', views.OpportunityDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.OpportunityUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.OpportunityDeleteView.as_view(), name='delete'),
    path('<int:pk>/comment/', views.AddCommentView.as_view(), name='add_comment'),
    path('<int:opportunity_id>/comment/<int:comment_id>/edit/', views.EditCommentView.as_view(), name='edit_comment'),
    path('<int:opportunity_id>/comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]
