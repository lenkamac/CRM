from django.urls import path
from . import views
from .views import CustomPasswordChangeView

app_name = 'userprofile'

urlpatterns = [
    path('', views.user_account, name='account'),
    path('edit/', views.edit_profile, name='edit-profile'),
    path('register/', views.register, name='register'),
    path('change-password/', CustomPasswordChangeView.as_view(), name='change-password'),
    path('delete-account/', views.delete_account, name='delete-account'),
]
