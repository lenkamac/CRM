document.addEventListener('DOMContentLoaded', function() {

    // Initialize flatpickr for date fields if flatpickr is available
    if (typeof flatpickr !== 'undefined') {
        // Set German locale globally or use explicit format
        const flatpickrConfig = {
            dateFormat: "d.m.Y",
            altInput: false,
            allowInput: true,
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
    }


    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: calendarEventsUrl,  // We'll define this in template!
        eventTimeFormat: {  // uppercase H for 24h, lowercase i for minutes
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        },
        // === Add this below your eventClick ===
        dateClick: function(info) {
            // Clear previous form values
            document.getElementById('addEventForm').reset();

            // Pre-fill the "Start Date" field with clicked date in dd.mm.yyyy format
            const clickedDate = new Date(info.dateStr);
            const day = String(clickedDate.getDate()).padStart(2, '0');
            const month = String(clickedDate.getMonth() + 1).padStart(2, '0');
            const year = clickedDate.getFullYear();
            document.getElementById('eventStartDate').value = `${day}.${month}.${year}`;
            document.getElementById('eventStartTime').value = "09:00";

            // Show the add event modal
            var addModal = new bootstrap.Modal(document.getElementById('addEventModal'));
            addModal.show();
        },

        eventClick: function(info) {
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
                document.getElementById('editEventId').value = info.event.id;
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
                    fetch(`delete_event/${info.event.id}/`, {
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

        fetch(`update_event/${eventId}/`, {
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

// upcomming events
document.addEventListener('DOMContentLoaded', function () {
    loadUpcomingEvents();
    fetch(calendarEventsUrl)
        .then(response => response.json())
        .then(function(events) {
            const now = new Date();
            // Sort upcoming events by start (asc)
            const upcoming = events
                .filter(ev => new Date(ev.start) >= now)
                .sort((a, b) => new Date(a.start) - new Date(b.start))
                .slice(0, 5); // Only show next 5 by default. Adjust if needed

            const ul = document.getElementById('upcoming-events-list');
            ul.innerHTML = ""; // Clear old contents

            upcoming.forEach(event => {
                const li = document.createElement('li');
                li.classList.add('list-group-item');

                // Add end time if available. You can change format as needed
                let display = `<strong>${event.title}</strong><br>
                    <small>Start: ${formatDateDisplay(event.start)}</small><br>`;
                if (event.end) {
                    display += `<br><small>End: ${formatDateDisplay(event.end)}</small>`;
                }
                // Add the description under the date section, if it exists
                if (event.description) {
                    display += `<br><small class="text-muted">${event.description}</small>`;
                }

                li.innerHTML = display;
                ul.appendChild(li);
            });

            if (upcoming.length === 0) {
                ul.innerHTML = '<li class="list-group-item">No upcoming events!</li>';
            }
        });
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
            // Find event ensuring ID comparison matches (string to string)
            const event = events.find(e => String(e.id) === String(eventId));

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
            // Ensure ID comparison works (casting to string)
            const event = events.find(e => String(e.id) === String(eventId));

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
        fetch(`delete_event/${eventId}/`, {
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