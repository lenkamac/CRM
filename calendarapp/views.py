import json
from datetime import datetime, time

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Event
from task.models import Task


# html page for event and calendar
def calendar_view(request):

    return render(request, 'calendarapp/calendar.html')


# events
def events_json(request):
    events = []
    for event in Event.objects.all():
        events.append({
            'id': f'event-{event.id}',
            'title': event.title,
            'start': event.start.isoformat(),
            'end': event.end.isoformat() if event.end else None,
            'description': event.description,
            'type': 'event',
        })

    # Add tasks
    for task in Task.objects.filter(due_date__isnull=False):
        # Combine due_date and due_time
        if task.due_time:
            start_dt = datetime.combine(task.due_date, task.due_time)
        else:
            start_dt = datetime.combine(task.due_date, time(0, 0))

        events.append({
            'id': f'task-{task.id}',
            'title': task.title,
            'start': start_dt.isoformat(),
            'description': f"Priority: {task.get_priority_display()}\nStatus: {task.get_status_display()}\nAssigned to: {task.assigned_to.get_full_name() if task.assigned_to else 'Unassigned'}",
            'priority': task.priority,
            'status': task.status,
            'assigned_to': task.assigned_to.username if task.assigned_to else None,
            'type': 'task',
            'backgroundColor': 'red' if task.priority == 'high' else 'orange' if task.priority == 'medium' else 'green',
        })
    return JsonResponse(events, safe=False)


# add event
@csrf_exempt
def add_event(request):
    if request.method == "POST":
        data = json.loads(request.body)
        Event.objects.create(
            title=data.get('title'),
            start=data.get('start'),
            end=data.get('end') or None,
            description=data.get('description')
        )
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# delete event
@csrf_exempt
def delete_event(request, event_id):
    if request.method == "DELETE":
        try:
            event = Event.objects.get(id=event_id)
            event.delete()
            return JsonResponse({'success': True})
        except Event.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Event not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# edit event
@csrf_exempt
def update_event(request, event_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            event = Event.objects.get(id=event_id)
            event.title = data.get('title')
            event.start = data.get('start')
            event.end = data.get('end') or None
            event.description = data.get('description')
            event.save()
            return JsonResponse({'success': True})
        except Event.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Event not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# paginator for upcoming events
def upcoming_events_json(request):
    page_number = int(request.GET.get('page', 1))
    page_size = 5
    # Only get events that start now or in the future, ordered by soonest first
    upcoming_events_qs = Event.objects.filter(start__gte=timezone.now()).order_by('start', 'id')
    paginator = Paginator(upcoming_events_qs, page_size)
    page_obj = paginator.get_page(page_number)
    events = []
    for event in page_obj.object_list:
        events.append({
            'id': event.id,
            'title': event.title,
            'start': event.start.isoformat(),
            'end': event.end.isoformat() if event.end else None,
            'description': event.description,
        })
    return JsonResponse({
        'events': events,
        'page': page_obj.number,
        'num_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_prev': page_obj.has_previous(),
    })


# paginator for all tasks
def all_tasks_json(request):
    page_number = int(request.GET.get('page', 1))
    page_size = 5
    # Get all tasks ordered by due_date
    all_tasks_qs = Task.objects.filter(due_date__isnull=False).order_by('due_date', 'due_time', 'id')
    paginator = Paginator(all_tasks_qs, page_size)
    page_obj = paginator.get_page(page_number)
    tasks = []
    for task in page_obj.object_list:
        # Combine due_date and due_time
        if task.due_time:
            start_dt = datetime.combine(task.due_date, task.due_time)
        else:
            start_dt = datetime.combine(task.due_date, time(0, 0))

        tasks.append({
            'id': f'task-{task.id}',
            'title': task.title,
            'start': start_dt.isoformat(),
            'priority': task.priority,
            'status': task.status,
            'assigned_to': task.assigned_to.username if task.assigned_to else None,
            'type': 'task',
        })
    return JsonResponse({
        'tasks': tasks,
        'page': page_obj.number,
        'num_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_prev': page_obj.has_previous(),
    })