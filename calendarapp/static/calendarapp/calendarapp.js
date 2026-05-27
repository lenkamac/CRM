let calendar;
let pendingClickedDate = null;
let pendingFormModalId = null;

document.addEventListener('DOMContentLoaded', function() {

    // Initialize flatpickr for date fields if flatpickr is available
    if (typeof flatpickr !== 'undefined') {
        // Set German locale globally or use explicit format
        const flatpickrConfig = {
            dateFormat: "d.m.Y",
            altInput: false,
            allowInput: true,
            static: true,
            autocomplete: false,
            // Parse input in dd.mm.yyyy format
            parseDate: (datestr, format) => {
                const parts = datestr.split('.');
                if (parts.length === 3) {
                    const day = parseInt(parts[0], 10);
                    const month = parseInt(parts[1], 10) - 1;
                    const year = parseInt(parts[2], 10);
                    return new Date(year, month, day);
                }
                return new Date(datestr);
            },
            // Format output as dd.mm.yyyy
            formatDate: (date, format) => {
                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const year = date.getFullYear();
                return `${day}.${month}.${year}`;
            }
        };

        flatpickr("#eventStartDate", flatpickrConfig);
        flatpickr("#eventEndDate", flatpickrConfig);
        flatpickr("#editEventStartDate", flatpickrConfig);
        flatpickr("#editEventEndDate", flatpickrConfig);
        flatpickr("#taskDueDate", flatpickrConfig);

        const timeConfig = {
            enableTime: true,
            noCalendar: true,
            dateFormat: "H:i",
            time_24hr: true,
            static: true,
        };
        flatpickr("#taskDueTime", timeConfig);
        flatpickr("#editEventStartTime", timeConfig);
        flatpickr("#editEventEndTime", timeConfig);
        flatpickr("#eventStartTime", timeConfig);
        flatpickr("#eventEndTime", timeConfig);
    }


    var calendarEl = document.getElementById('calendar');
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        firstDay: 1,  // Monday (0=Sunday, 1=Monday, etc.)
        events: calendarEventsUrl,  // We'll define this in template!
        eventTimeFormat: {  // uppercase H for 24h, lowercase i for minutes
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        },
        dateClick: function(info) {
            pendingClickedDate = info.dateStr;
            var choiceModal = new bootstrap.Modal(document.getElementById('dateClickChoiceModal'));
            choiceModal.show();
        },

        eventClick: function(info) {
            // Check if this is a task
            const isTask = info.event.extendedProps.type === 'task';

            if (isTask) {
                // For tasks, show task details directly
                let taskDetails = `<strong>${info.event.title}</strong><br>`;
                taskDetails += `<small>Due: ${formatDateDisplay(info.event.start)}</small><br>`;
                if (info.event.extendedProps.priority) {
                    taskDetails += `<small>Priority: ${info.event.extendedProps.priority}</small><br>`;
                }
                if (info.event.extendedProps.status) {
                    taskDetails += `<small>Status: ${info.event.extendedProps.status}</small><br>`;
                }
                if (info.event.extendedProps.assigned_to) {
                    taskDetails += `<small>Assigned to: ${info.event.extendedProps.assigned_to}</small><br>`;
                }
                if (info.event.extendedProps.description) {
                    taskDetails += `<br><small class="text-muted">${info.event.extendedProps.description}</small>`;
                }

                alert(taskDetails.replace(/<br>/g, '\n').replace(/<\/?[^>]+(>|$)/g, ""));
                return;
            }

            // Store event id and title in the modal for easy access
            document.getElementById('eventActionEventId').value = info.event.id;
            document.getElementById('eventActionModalTitle').textContent = info.event.title;
            document.getElementById('detailEventBtn').onclick = function() {
            // Fill in the details modal with the event's data
            document.getElementById('detailEventTitle').textContent = info.event.title || '';
            document.getElementById('detailEventStart').textContent = info.event.start ? formatDateDisplay(info.event.start) : '';
            document.getElementById('detailEventEnd').textContent = info.event.end ? formatDateDisplay(info.event.end) : 'No end';
            document.getElementById('detailEventDesc').textContent = info.event.extendedProps.description || '';

            actionModal.hide();
            var detailModal = new bootstrap.Modal(document.getElementById('eventDetailModal'));
            detailModal.show();
        };


            // Open action modal
            var actionModal = new bootstrap.Modal(document.getElementById('eventActionModal'));
            actionModal.show();

            // Remove any old listeners to avoid stacking
            document.getElementById('editEventBtn').onclick = function() {
                actionModal.hide();
                // Prefill and show the edit modal
                // Extract the actual event ID (remove 'event-' prefix)
                const actualId = info.event.id.replace('event-', '');
                document.getElementById('editEventId').value = actualId;
                document.getElementById('editEventTitle').value = info.event.title;

                // Split datetime into date and time parts
                const startDateTime = splitDateTime(info.event.start);
                document.getElementById('editEventStartDate').value = startDateTime.date;
                document.getElementById('editEventStartTime').value = startDateTime.time;

                if (info.event.end) {
                    const endDateTime = splitDateTime(info.event.end);
                    document.getElementById('editEventEndDate').value = endDateTime.date;
                    document.getElementById('editEventEndTime').value = endDateTime.time;
                } else {
                    document.getElementById('editEventEndDate').value = '';
                    document.getElementById('editEventEndTime').value = '';
                }

                document.getElementById('editEventDesc').value = info.event.extendedProps.description || "";
                var editModal = new bootstrap.Modal(document.getElementById('editEventModal'));
                editModal.show();
            };

            document.getElementById('deleteEventBtn').onclick = function() {
                actionModal.hide();
                if (confirm('Are you sure you want to delete this event?')) {
                    // Extract the actual event ID (remove 'event-' prefix)
                    const actualId = info.event.id.replace('event-', '');
                    fetch(`delete_event/${actualId}/`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            info.event.remove();
                            alert('Event deleted.');
                            refreshUpcomingEvents();
                        } else {
                            alert('Failed to delete event.');
                        }
                    })
                    .catch(() => alert('Error deleting event.'));
                }
            };
        },
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek, multiMonthYear',
        }
    });
    calendar.render();


    // Add-event form handler
    document.getElementById('addEventForm').addEventListener('submit', function(e) {
        e.preventDefault();

        // Combine date and time fields
        const startDateTime = combineDateTimeToISO(
            document.getElementById('eventStartDate').value,
            document.getElementById('eventStartTime').value
        );
        const endDateTime = combineDateTimeToISO(
            document.getElementById('eventEndDate').value,
            document.getElementById('eventEndTime').value
        );

        // Gather form data
        var formData = {
            title: document.getElementById('eventTitle').value,
            start: startDateTime,
            end: endDateTime,
            description: document.getElementById('eventDesc').value,
        };

        fetch('add_event/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Network error.');
        })
        .then(data => {
            if (data.success) {
                // Optionally refresh the calendar:
                calendar.refetchEvents();
                refreshUpcomingEvents();
                // Hide modal
                var addEventModal = document.getElementById('addEventModal');
                var modalInstance = bootstrap.Modal.getInstance(addEventModal);
                modalInstance.hide();
                // Optionally clear form
                e.target.reset();
            } else {
                alert('Failed to add event.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error adding event');
        });
    });


    // Handle edit form submit
    document.getElementById('editEventForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const eventId = document.getElementById('editEventId').value;
        // Extract numeric ID from 'event-123' format
        const numericId = eventId.replace('event-', '');

        // Combine date and time fields
        const startDateTime = combineDateTimeToISO(
            document.getElementById('editEventStartDate').value,
            document.getElementById('editEventStartTime').value
        );
        const endDateTime = combineDateTimeToISO(
            document.getElementById('editEventEndDate').value,
            document.getElementById('editEventEndTime').value
        );

        const data = {
            title: document.getElementById('editEventTitle').value,
            start: startDateTime,
            end: endDateTime,
            description: document.getElementById('editEventDesc').value,
        };

        fetch(`update_event/${numericId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                calendar.refetchEvents();
                refreshUpcomingEvents();
                bootstrap.Modal.getInstance(document.getElementById('editEventModal')).hide();
            } else {
                alert('Failed to update event');
            }
        });
    });

    // Choice modal: open the right form after the choice modal is fully hidden
    document.getElementById('dateClickChoiceModal').addEventListener('hidden.bs.modal', function() {
        if (pendingFormModalId) {
            var formModal = new bootstrap.Modal(document.getElementById(pendingFormModalId));
            formModal.show();
            pendingFormModalId = null;
        }
    });

    // Set a flatpickr-controlled input to a date from yyyy-mm-dd string
    function setFlatpickrDate(elementId, isoDateStr) {
        const el = document.getElementById(elementId);
        if (el && el._flatpickr) {
            el._flatpickr.setDate(isoDateStr);
        } else if (el) {
            // Fallback: convert yyyy-mm-dd → dd.mm.yyyy
            const parts = isoDateStr.split('-');
            if (parts.length === 3) {
                el.value = `${parts[2]}.${parts[1]}.${parts[0]}`;
            }
        }
    }

    document.getElementById('choiceAddEventBtn').addEventListener('click', function() {
        document.getElementById('addEventForm').reset();
        if (pendingClickedDate) {
            setFlatpickrDate('eventStartDate', pendingClickedDate);
            document.getElementById('eventStartTime').value = "09:00";
        }
        pendingFormModalId = 'addEventModal';
        bootstrap.Modal.getInstance(document.getElementById('dateClickChoiceModal')).hide();
    });

    document.getElementById('choiceAddTaskBtn').addEventListener('click', function() {
        document.getElementById('addTaskForm').reset();
        if (pendingClickedDate) {
            setFlatpickrDate('taskDueDate', pendingClickedDate);
        }
        pendingFormModalId = 'addTaskModal';
        bootstrap.Modal.getInstance(document.getElementById('dateClickChoiceModal')).hide();
    });

    // Populate client/lead selects when add task modal opens
    document.getElementById('addTaskModal').addEventListener('show.bs.modal', function() {
        fetch(clientsLeadsUrl)
            .then(r => r.json())
            .then(data => {
                const clientSel = document.getElementById('taskClient');
                const leadSel = document.getElementById('taskLead');
                // keep first empty option, replace the rest
                clientSel.innerHTML = '<option value="">---------</option>';
                leadSel.innerHTML = '<option value="">---------</option>';
                data.clients.forEach(c => {
                    const label = [c.first_name, c.last_name].filter(Boolean).join(' ') || c.company || `Client #${c.id}`;
                    clientSel.innerHTML += `<option value="${c.id}">${label}</option>`;
                });
                data.leads.forEach(l => {
                    const label = [l.first_name, l.last_name].filter(Boolean).join(' ') || l.company || `Lead #${l.id}`;
                    leadSel.innerHTML += `<option value="${l.id}">${label}</option>`;
                });
            });
    });

    // Selecting a client clears lead and vice versa
    document.getElementById('taskClient').addEventListener('change', function() {
        if (this.value) document.getElementById('taskLead').value = '';
    });
    document.getElementById('taskLead').addEventListener('change', function() {
        if (this.value) document.getElementById('taskClient').value = '';
    });

    // Add task form submit handler
    document.getElementById('addTaskForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const dueDateDmy = document.getElementById('taskDueDate').value;
        const parts = dueDateDmy.split('.');
        const dueDateISO = parts.length === 3 ? `${parts[2]}-${parts[1]}-${parts[0]}` : dueDateDmy;

        const formData = {
            title: document.getElementById('taskTitle').value,
            due_date: dueDateISO,
            due_time: document.getElementById('taskDueTime').value || null,
            priority: document.getElementById('taskPriority').value,
            status: document.getElementById('taskStatus').value,
            description: document.getElementById('taskDesc').value,
            client_id: document.getElementById('taskClient').value || null,
            lead_id: document.getElementById('taskLead').value || null,
        };

        fetch('add_task/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (response.ok) return response.json();
            throw new Error('Network error.');
        })
        .then(data => {
            if (data.success) {
                calendar.refetchEvents();
                loadAllTasks();
                bootstrap.Modal.getOrCreateInstance(document.getElementById('addTaskModal')).hide();
                e.target.reset();
            } else {
                alert('Failed to add task.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error adding task');
        });
    });

    // Drag & Drop/resize logic
    function updateEvent(info) {
        fetch(`update_event/${info.event.id}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                title: info.event.title,
                start: info.event.start.toISOString(),
                end: info.event.end ? info.event.end.toISOString() : null,
                description: info.event.extendedProps.description
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert('Failed to update event');
                info.revert(); // Revert to original position
            }
        });
    }


});

// Helper function to combine date (dd.mm.yyyy) and time (HH:MM) into ISO string
function combineDateTimeToISO(dateStr, timeStr) {
    if (!dateStr || !timeStr) return null;

    // Parse date from dd.mm.yyyy format
    const dateParts = dateStr.split('.');
    if (dateParts.length !== 3) return null;

    const day = parseInt(dateParts[0], 10);
    const month = parseInt(dateParts[1], 10) - 1; // Month is 0-indexed
    const year = parseInt(dateParts[2], 10);

    // Parse time from HH:MM format
    const timeParts = timeStr.split(':');
    if (timeParts.length !== 2) return null;

    const hours = parseInt(timeParts[0], 10);
    const minutes = parseInt(timeParts[1], 10);

    // Create date object and convert to ISO
    const dateTime = new Date(year, month, day, hours, minutes);
    return dateTime.toISOString();
}

// Helper function to split ISO datetime into date (dd.mm.yyyy) and time (HH:MM)
function splitDateTime(isoString) {
    if (!isoString) return { date: '', time: '' };

    const d = new Date(isoString);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');

    return {
        date: `${day}.${month}.${year}`,
        time: `${hours}:${minutes}`
    };
}


// format for date and time display (dd.mm.yyyy HH:MM in 24-hour format)
function formatDateDisplay(dateString) {
    const d = new Date(dateString);
    const pad = n => n < 10 ? '0' + n : n;
    return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()} ` +
           `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}


function localToUTC(dateLocalString) {
    if (!dateLocalString) return null; // Return null for blank inputs (e.g., end date)
    const local = new Date(dateLocalString);
    if (isNaN(local)) return null;     // Also cover any invalid date
    return local.toISOString();
}

// Helper to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// paginated tasks
function loadAllTasks(page=1) {
    fetch(`all_tasks/?page=${page}`)
        .then(response => response.json())
        .then(data => {
            const ul = document.getElementById('upcoming-tasks-list');
            ul.innerHTML = '';

            data.tasks.forEach(task => {
                const li = document.createElement('li');
                li.classList.add('list-group-item');

                // Extract numeric ID from 'task-123' format
                const taskId = task.id.replace('task-', '');

                // Priority badge color
                const priorityColor = getPriorityColor(task.priority);

                // Status badge color
                let statusColor = 'secondary';
                if (task.status === 'completed') statusColor = 'success';
                else if (task.status === 'in_progress') statusColor = 'primary';
                else if (task.status === 'canceled') statusColor = 'dark';

                let display = `
                    <div class="d-flex justify-content-between align-items-start w-100">
                        <div class="flex-grow-1">`;

                if (task.client_or_lead && task.client_or_lead_type && task.client_or_lead_id) {
                    const relatedText = task.client_or_lead_type === 'client' ? 'Related to Client' : 'Related to Lead';
                    const detailUrl = task.client_or_lead_type === 'client'
                        ? `/dashboard/clients/${task.client_or_lead_id}/`
                        : `/dashboard/leads/${task.client_or_lead_id}/`;
                    display += `<div class="text-muted" style="font-size: 0.95rem;">${relatedText}: <a href="${detailUrl}" class="text-decoration-none fw-semibold">${task.client_or_lead}</a></div>`;
                }

                display += `<strong>${task.title}</strong><br>
                            Due: ${formatDateDisplay(task.start)}<br>`;

                if (task.priority) {
                    display += `<span class="badge bg-${priorityColor} me-1">${task.priority}</span>`;
                }
                if (task.status) {
                    display += `<span class="badge bg-${statusColor}">${task.status}</span>`;
                }
                if (task.assigned_to) {
                    display += `<br><small class="text-muted">Assigned to: ${task.assigned_to}</small>`;
                }

                display += `
                        </div>
                        <div class="task-actions d-flex gap-1 ms-2">
                            <button class="btn btn-sm btn-outline-info p-1" onclick="showTaskDetail('${taskId}')" title="View">
                                <i class="bi bi-info-circle" style="font-size: 0.8rem;"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-primary p-1" onclick="editTask('${taskId}')" title="Edit">
                                <i class="bi bi-pencil-square"  style="font-size: 0.8rem;"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger p-1" onclick="deleteTask('${taskId}')" title="Delete">
                                <i class="bi bi-trash3" style="font-size: 0.8rem;"></i>
                            </button>
                        </div>
                    </div>
                `;

                li.innerHTML = display;
                ul.appendChild(li);
            });

            // Pagination controls
            const paginationDiv = document.getElementById('tasks-pagination');
            paginationDiv.innerHTML = '';
            if (data.has_prev) {
                const prevBtn = document.createElement('button');
                prevBtn.className = 'btn btn-secondary btn-sm me-2';
                prevBtn.textContent = 'Previous';
                prevBtn.onclick = () => {
                    loadAllTasks(data.page - 1);
                };
                paginationDiv.appendChild(prevBtn);
            }
            if (data.has_next) {
                const nextBtn = document.createElement('button');
                nextBtn.className = 'btn btn-secondary btn-sm';
                nextBtn.textContent = 'Next';
                nextBtn.onclick = () => {
                    loadAllTasks(data.page + 1);
                };
                paginationDiv.appendChild(nextBtn);
            }

            if (data.tasks.length === 0) {
                ul.innerHTML = '<li class="list-group-item">No tasks!</li>';
            }
        });
}

// Add Task button handler
document.addEventListener('DOMContentLoaded', function() {
    const addTaskBtn = document.getElementById('add-task-btn');
    if (addTaskBtn) {
        addTaskBtn.addEventListener('click', function() {
            document.getElementById('addTaskForm').reset();
            pendingClickedDate = null;
            var addModal = new bootstrap.Modal(document.getElementById('addTaskModal'));
            addModal.show();
        });
    }
});

// upcomming events
document.addEventListener('DOMContentLoaded', function () {
    loadUpcomingEvents();
    loadAllTasks();
});

let currentPage = 1;

function loadUpcomingEvents(page=1) {
    fetch(`upcoming_events/?page=${page}`)
        .then(response => response.json())
        .then(data => {
            const ul = document.getElementById('upcoming-events-list');
            ul.innerHTML = '';
            data.events.forEach(event => {
                const li = document.createElement('li');
                li.classList.add('list-group-item',  'd-flex', 'justify-content-between', 'align-items-center', 'flex-wrap');

                let display = `
                    <div class="event-info flex-grow-1 text-start">
                        <strong>${event.title}</strong><br>
                        <small>Start: ${formatDateDisplay(event.start)}</small>
                `;
                if (event.end) {
                    display += `<br><small>End: ${formatDateDisplay(event.end)}</small>`;
                }
                if (event.description) {
                    display += `<br><small class="text-muted d-block text-truncate" style="max-width: 200px;">${event.description}</small>`;
                }
                display += `</div>`;

                // Action Buttons
                display += `
                    <div class="event-actions d-flex gap-1 mt-1 mt-sm-0">
                        <button class="btn btn-sm btn-outline-info p-1" onclick="showEventDetail('${event.id}')" title="View">
                            <i class="bi bi-info-circle"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-primary p-1" onclick="openEditModal('${event.id}')" title="Edit">
                            <i class="bi bi-pencil-square"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger p-1" onclick="deleteEvent('${event.id}')" title="Delete">
                            <i class="bi bi-trash3"></i>
                        </button>
                    </div>
                `;
                li.innerHTML = display;
                ul.appendChild(li);
            });

            // Pagination controls
            const paginationDiv = document.getElementById('upcoming-pagination');
            paginationDiv.innerHTML = '';
            if (data.has_prev) {
                const prevBtn = document.createElement('button');
                prevBtn.className = 'btn btn-secondary btn-sm me-2';
                prevBtn.textContent = 'Previous';
                prevBtn.onclick = () => {
                    loadUpcomingEvents(data.page - 1);
                };
                paginationDiv.appendChild(prevBtn);
            }
            if (data.has_next) {
                const nextBtn = document.createElement('button');
                nextBtn.className = 'btn btn-secondary btn-sm';
                nextBtn.textContent = 'Next';
                nextBtn.onclick = () => {
                    loadUpcomingEvents(data.page + 1);
                };
                paginationDiv.appendChild(nextBtn);
            }
            currentPage = data.page;
        });
}

function refreshUpcomingEvents() {
    loadUpcomingEvents(1); // Always load first page, or pass desired page
}

// --- Global functions for Action Buttons ---

function showEventDetail(eventId) {
    // Fetch event data using the global URL variable
    fetch(calendarEventsUrl)
        .then(response => response.json())
        .then(events => {
            // Filter only events (not tasks) and find the event
            const event = events.filter(e => e.type === 'event').find(e => String(e.id) === String(eventId));

            if (event) {
                // Fill in the details modal with the event's data
                document.getElementById('detailEventTitle').textContent = event.title || '';
                document.getElementById('detailEventStart').textContent = event.start ? formatDateDisplay(event.start) : '';
                document.getElementById('detailEventEnd').textContent = event.end ? formatDateDisplay(event.end) : 'No end';
                document.getElementById('detailEventDesc').textContent = event.description || 'No description';

                // Show the details modal using Bootstrap's modern instance method
                var detailModalEl = document.getElementById('eventDetailModal');
                var modalInstance = bootstrap.Modal.getOrCreateInstance(detailModalEl);
                modalInstance.show();
            } else {
                console.error("Event detail not found for ID:", eventId);
            }
        })
        .catch(err => console.error("Error loading event details:", err));
}

function openEditModal(eventId) {
    // Fetch the list of events to find the specific one
    fetch(calendarEventsUrl)
        .then(response => response.json())
        .then(events => {
            // Filter only events (not tasks) and find the event
            const event = events.filter(e => e.type === 'event').find(e => String(e.id) === String(eventId));

            if (event) {
                document.getElementById('editEventId').value = event.id;
                document.getElementById('editEventTitle').value = event.title;

                // Split datetime into date and time parts
                const startDateTime = splitDateTime(event.start);
                document.getElementById('editEventStartDate').value = startDateTime.date;
                document.getElementById('editEventStartTime').value = startDateTime.time;

                if (event.end) {
                    const endDateTime = splitDateTime(event.end);
                    document.getElementById('editEventEndDate').value = endDateTime.date;
                    document.getElementById('editEventEndTime').value = endDateTime.time;
                } else {
                    document.getElementById('editEventEndDate').value = '';
                    document.getElementById('editEventEndTime').value = '';
                }

                document.getElementById('editEventDesc').value = event.description || "";

                // Show the modal
                var editModalEl = document.getElementById('editEventModal');
                var modalInstance = bootstrap.Modal.getOrCreateInstance(editModalEl);
                modalInstance.show();
            } else {
                console.error("Event not found with ID:", eventId);
            }
        })
        .catch(err => console.error("Error loading event for edit:", err));
}

function deleteEvent(eventId) {
    if (confirm('Are you sure you want to delete this event?')) {
        // Extract numeric ID from 'event-123' format
        const numericId = eventId.replace('event-', '');

        fetch(`delete_event/${numericId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Event deleted.');
                refreshUpcomingEvents();
                // Also refresh the calendar if it exists on the page
                const calendarEl = document.getElementById('calendar');
                if (calendarEl) {
                    location.reload(); // Quickest way to sync both views
                }
            } else {
                alert('Failed to delete event.');
            }
        })
        .catch(() => alert('Error deleting event.'));
    }
}

// --- Task Action Functions ---

function showTaskDetail(taskId) {
    // Fetch task data
    fetch(calendarEventsUrl)
        .then(response => response.json())
        .then(events => {
            // Filter only tasks and find the specific task
            const task = events.filter(e => e.type === 'task').find(e => String(e.id).replace('task-', '') === String(taskId));

            if (task) {
                // Fill in the task details modal
                let detailsHtml = `<p><strong>Title:</strong> ${task.title}</p>`;
                detailsHtml += `<p><strong>Due:</strong> ${formatDateDisplay(task.start)}</p>`;

                if (task.priority) {
                    detailsHtml += `<p><strong>Priority:</strong> <span class="badge bg-${getPriorityColor(task.priority)}">${task.priority}</span></p>`;
                }

                if (task.status) {
                    detailsHtml += `<p><strong>Status:</strong> <span class="badge bg-${getStatusColor(task.status)}">${task.status}</span></p>`;
                }

                if (task.assigned_to) {
                    detailsHtml += `<p><strong>Assigned to:</strong> ${task.assigned_to}</p>`;
                }

                if (task.description) {
                    detailsHtml += `<p><strong>Description:</strong> ${task.description}</p>`;
                }

                // Show the details in a modal
                document.getElementById('taskDetailModalBody').innerHTML = detailsHtml;
                var taskDetailModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('taskDetailModal'));
                taskDetailModal.show();
            } else {
                console.error("Task not found for ID:", taskId);
            }
        })
        .catch(err => console.error("Error loading task details:", err));
}

function editTask(taskId) {
    // Redirect to edit page with return parameter
    window.location.href = `/dashboard/tasks/${taskId}/edit/?next=${encodeURIComponent(window.location.pathname)}`;
}

function deleteTask(taskId) {
    if (confirm('Are you sure you want to delete this task?')) {
        // Create form data to send the next URL
        const formData = new FormData();
        formData.append('next', window.location.pathname);

        fetch(`/dashboard/tasks/${taskId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: formData
        })
        .then(response => {
            if (response.ok) {
                loadAllTasks();
                const calendarEl = document.getElementById('calendar');
                if (calendarEl && typeof calendar !== 'undefined') {
                    calendar.refetchEvents();
                }
            } else {
                alert('Failed to delete task.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting task.');
        });
    }
}

// Helper functions for badge colors
function getPriorityColor(priority) {
    if (priority === 'urgent') return 'danger';
    if (priority === 'high') return 'orange';
    if (priority === 'medium') return 'success';
    if (priority === 'low') return 'primary';
    return 'secondary';
}

function getStatusColor(status) {
    if (status === 'completed') return 'success';
    if (status === 'in_progress') return 'primary';
    if (status === 'canceled') return 'dark';
    return 'secondary';
}
