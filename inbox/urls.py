from django.urls import path

from . import views

app_name = 'inbox'

urlpatterns = [
    path('', views.inbox_list, name='list'),
    path('compose/', views.inbox_compose, name='compose'),
    path('sync/', views.inbox_sync, name='sync'),
    path('bulk/', views.inbox_bulk_action, name='bulk_action'),
    path('<int:pk>/', views.inbox_detail, name='detail'),
    path('<int:pk>/reply/', views.inbox_reply, name='reply'),
    path('<int:pk>/toggle-read/', views.inbox_toggle_read, name='toggle_read'),
    path('<int:pk>/toggle-star/', views.inbox_toggle_star, name='toggle_star'),
    path('<int:pk>/delete/', views.inbox_delete, name='delete'),
    path('<int:pk>/link/', views.inbox_link_contact, name='link_contact'),
    path('attachment/<int:pk>/', views.inbox_attachment, name='attachment'),
]
