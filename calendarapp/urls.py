from django.urls import path
from . import views


app_name = 'calendarapp'

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('events/', views.events_json, name='events_json'),
    path('add_event/', views.add_event, name='add_event'),
    path('delete_event/<int:event_id>/', views.delete_event, name='delete_event'),
    path('update_event/<int:event_id>/', views.update_event, name='update_event'),
    path('add_task/', views.add_task, name='add_task'),
    path('upcoming_events/', views.upcoming_events_json, name='upcoming_events_json'),
    path('all_tasks/', views.all_tasks_json, name='all_tasks_json'),
]
