// Automatically hide alert messages after 3 seconds (3000 milliseconds)
document.addEventListener('DOMContentLoaded', function() {
setTimeout(function() {
  document.querySelectorAll('.alert').forEach(function(alert) {
    // Fade out for a smooth effect (optional)
    alert.style.transition = "opacity 0.5s linear";
    alert.style.opacity = 0;
    setTimeout(function() { alert.remove(); }, 500); // remove from DOM after fade out
  });
}, 3000); // Show message for 3 seconds


  if(document.querySelector("#id_due_date")&&typeof flatpickr !== "undefined") {
    flatpickr("#id_due_date", {
            dateFormat: "d.m.Y",
            allowInput: true,
            static: true,
            autocomplete: false,
            locale: { firstDayOfWeek: 1 }
        });
  }

  if(document.querySelector("#id_due_time") && typeof flatpickr !== "undefined") {
    flatpickr("#id_due_time", {
            enableTime: true,
            noCalendar: true,
            dateFormat: "H:i",
            time_24hr: true,
            allowInput: true,
            static: true,
            autocomplete: false
        });
  }

});
