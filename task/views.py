from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

from client.models import Client
from lead.models import Lead
from .forms import TaskForm, TaskCommentForm
from .models import Task, TaskComment


# Create your views here.
# Task list view function
@login_required
def tasks(request):
    from django.db.models import Q

    # Get all users for the filter dropdown
    users = User.objects.all()

    # Get tasks with filters
    tasks_list = Task.objects.all()

    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        tasks_list = tasks_list.filter(
            Q(client__company__icontains=search_query) |
            Q(client__last_name__icontains=search_query) |
            Q(lead__company__icontains=search_query) |
            Q(lead__last_name__icontains=search_query)
        )

    # Apply filters
    status_list = request.GET.getlist('status')
    if status_list:
        tasks_list = tasks_list.filter(status__in=status_list)
    else:
        tasks_list = tasks_list.filter(status__in=['todo', 'in_progress'])

    priority = request.GET.get('priority')
    if priority:
        tasks_list = tasks_list.filter(priority=priority)

    assigned_to = request.GET.get('assigned_to')
    if assigned_to:
        tasks_list = tasks_list.filter(assigned_to_id=assigned_to)

    related_to = request.GET.get('related_to')
    if related_to == "lead":
        tasks_list = tasks_list.filter(lead__isnull=False)
    elif related_to == "client":
        tasks_list = tasks_list.filter(client__isnull=False)
    elif related_to == "none":
        tasks_list = tasks_list.filter(lead__isnull=True, client__isnull=True)

    # Due date filter
    from datetime import date, timedelta
    due_date_filter = request.GET.get('due_date')
    if due_date_filter:
        today = date.today()
        if due_date_filter == "overdue":
            tasks_list = tasks_list.filter(due_date__lt=today)
        elif due_date_filter == "today":
            tasks_list = tasks_list.filter(due_date=today)
        elif due_date_filter == "this_week":
            week_end = today + timedelta(days=7)
            tasks_list = tasks_list.filter(due_date__gte=today, due_date__lte=week_end)
        elif due_date_filter == "this_month":
            month_end = date(today.year, today.month + 1 if today.month < 12 else 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
            tasks_list = tasks_list.filter(due_date__gte=today, due_date__lt=month_end)

    # Sorting
    sort_by = request.GET.get('sort', 'due_date')
    sort_order = request.GET.get('order', 'asc')
    order_prefix = '' if sort_order == 'asc' else '-'
    tasks_list = tasks_list.order_by(f'{order_prefix}{sort_by}')

    # Pagination
    paginator = Paginator(tasks_list, 10)  # Show 10 tasks per page
    page = request.GET.get('page')
    tasks = paginator.get_page(page)

    context = {
        'tasks': tasks,
        'users': users,
        'search_query': search_query,
        'sort_by': sort_by,
        'sort_order': sort_order,
    }

    return render(request, 'task/task_list.html', context)


# Task detail view function, with comments and files attached to the task.
@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task_comments = TaskComment.objects.filter(task_id=pk)
    form = TaskCommentForm()
    show_edit = False

    if request.method == 'POST' and 'edit_task' in request.POST:
        if not (request.user == task.created_by or request.user == task.assigned_to):
            raise PermissionDenied("You don't have permission to edit this task.")
        edit_form = TaskForm(request.POST, instance=task)
        if edit_form.is_valid():
            edit_form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('task:task_detail', pk=task.pk)
        show_edit = True
    else:
        edit_form = TaskForm(instance=task)

    return render(request, 'task/task_detail.html', {
        'task': task,
        'task_comments': task_comments,
        'form': form,
        'edit_form': edit_form,
        'show_edit': show_edit,
    })


# Add this new view function
@login_required
def task_add(request):
    next_url = request.POST.get('next') or request.GET.get('next')

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, 'Task was created successfully.')
            if next_url:
                return redirect(next_url)
            return redirect('task:task_list')
    else:
        initial_data = {}
        # Pre-fill lead or client if provided in URL parameters
        if 'lead_id' in request.GET:
            initial_data['lead'] = request.GET.get('lead_id')
        elif 'client_id' in request.GET:
            initial_data['client'] = request.GET.get('client_id')
        form = TaskForm(initial=initial_data)

    return render(request, 'task/task_form.html', {
        'form': form,
        'title': 'Add Task',
        'next': next_url
    })


# Delete task view function, with confirmation page.
@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)

    # Check if user has permission to delete the task
    if not (request.user == task.created_by or request.user == task.assigned_to):
        raise PermissionDenied("You don't have permission to delete this task.")

    if request.method == 'POST':
        task.delete()
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('task:task_list')

    return render(request, 'task/task_confirm_delete.html', {
        'task': task
    })


# Edit task view function, with confirmation page.
@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)

    # Check if user has permission to edit the task
    if not (request.user == task.created_by or request.user == task.assigned_to):
        raise PermissionDenied("You don't have permission to edit this task.")

    next_url = request.POST.get('next') or request.GET.get('next')

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            if next_url:
                return redirect(next_url)
            else:
                return redirect('task:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)

    return render(request, 'task/task_form.html', {
        'form': form,
        'title': 'Edit Task',
        'task': task,
        'next':next_url
    })


# task comment
@login_required
def add_task_comment(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.created_by = request.user
            comment.save()
            return redirect('task:task_detail', pk=task.pk)

    return redirect('task:task_detail', pk=task.pk)


# Edit task comment view function, with confirmation page.
@csrf_exempt
def edit_tasks_comment(request, comment_id):
    if request.method == "POST":
        comment = get_object_or_404(TaskComment, id=comment_id)

        # Check if the user is authorized to update the comment
        if request.user != comment.created_by:
            return JsonResponse({"error": "Unauthorized"}, status=403)

        new_content = request.POST.get("content", "")
        if new_content.strip() == "":
            return JsonResponse({"error": "Content cannot be empty"}, status=400)

        # Update the comment
        comment.content = new_content
        comment.save()
        return JsonResponse({"success": True, "updated_comment": comment.content})
    return JsonResponse({"error": "Invalid request"}, status=400)


# Delete task comment view function, with confirmation page.
@login_required
def delete_task_comment(request, comment_id):
    if request.method == "POST":
        comment = get_object_or_404(TaskComment, id=comment_id)

        # Check if the user is authorized to delete the comment
        if request.user != comment.created_by:
            return JsonResponse({"error": "Unauthorized"}, status=403)

        # Delete the comment
        comment.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def task_add_client(request, client_id):
    from datetime import datetime
    client = get_object_or_404(Client, pk=client_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        status = request.POST.get('status')
        due_date = request.POST.get('due_date') or None
        due_time = request.POST.get('due_time') or None

        # If due_time is an empty string, set it to None
        if due_time == '':
            due_time = None
        # If due_date is an empty string, set it to None
        if due_date == '':
            due_date = None

        # Convert date format from dd.mm.yyyy to YYYY-MM-DD
        if due_date:
            try:
                due_date = datetime.strptime(due_date, '%d.%m.%Y').strftime('%Y-%m-%d')
            except ValueError:
                pass  # If conversion fails, keep original format

        # Add other fields as needed
        if title:
            Task.objects.create(
                client=client,
                title=title,
                description=description,
                status=status,
                priority=priority,
                due_date=due_date,
                due_time=due_time,
                created_by=request.user,
            )
        return redirect('client:detail', client_id)

    return redirect('client:detail', client_id)

def task_comments_partial(request, pk):
    task = get_object_or_404(Task, pk=pk)
    comments = task.comments.all()
    # Return only the HTML for comments
    return render(request, 'task/partials/_comments.html', {'comments': comments})



@login_required
def task_add_lead(request, lead_id):
    from datetime import datetime
    lead = get_object_or_404(Lead, pk=lead_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        status = request.POST.get('status')
        due_date = request.POST.get('due_date') or None
        due_time = request.POST.get('due_time') or None

        # If due_time is an empty string, set it to None
        if due_time == '':
            due_time = None
        # If due_date is an empty string, set it to None
        if due_date == '':
            due_date = None

        # Convert date format from dd.mm.yyyy to YYYY-MM-DD
        if due_date:
            try:
                due_date = datetime.strptime(due_date, '%d.%m.%Y').strftime('%Y-%m-%d')
            except ValueError:
                pass  # If conversion fails, keep original format

        if title:
            Task.objects.create(
                lead=lead,
                title=title,
                description=description,
                priority=priority,
                status=status,
                due_date=due_date,
                due_time=due_time,
                created_by=request.user,
            )
        return redirect('lead:detail', lead_id)
    return redirect('lead:detail', lead_id)