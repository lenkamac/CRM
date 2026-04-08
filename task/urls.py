from django.urls import path
from task.views import *
from . import views


app_name = 'task'

urlpatterns = [
    path('', tasks, name='task_list'),
    path('<int:pk>/', task_detail, name='task_detail'),
    path('add/', task_add, name='task_add'),
    path('<int:pk>/edit/', task_edit, name='task_edit'),
    path('<int:pk>/delete/', task_delete, name='task_delete'),
    path('<int:pk>/comment/add/', views.add_task_comment, name='add_task_comment'),
    path("task_comment/edit/<int:comment_id>/", edit_tasks_comment, name="edit_tasks_comment"),
    path("task_comment/delete/<int:comment_id>/", delete_task_comment, name="delete_task_comment"),
    path('<int:client_id>/task/add/', views.task_add_client, name='task_add_client'),
    path('leads/<int:lead_id>/task/add/', views.task_add_lead, name='task_add_lead'),
    path('<int:pk>/comments-partial/', views.task_comments_partial, name='task_comments_partial'),
    path('autocomplete/', views.task_autocomplete, name='task_autocomplete'),
]
