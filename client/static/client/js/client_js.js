document.addEventListener('DOMContentLoaded', function () {
    const selectAllCheckbox = document.getElementById('select-all'); // Master checkbox
    const rowCheckboxes = document.querySelectorAll('.row-checkbox'); // All row checkboxes

    // Toggle all row checkboxes when the master checkbox is clicked
    selectAllCheckbox.addEventListener('change', function () {
        const isChecked = selectAllCheckbox.checked;
        rowCheckboxes.forEach((checkbox) => {
            checkbox.checked = isChecked;
        });
    });

    // Uncheck the master checkbox if any row checkbox is unchecked
    rowCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener('change', function () {
            if (!checkbox.checked) {
                selectAllCheckbox.checked = false;
            }
        });
    });

    // Check the master checkbox if all row checkboxes are checked
    rowCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener('change', function () {
            const allChecked = Array.from(rowCheckboxes).every((cb) => cb.checked);
            if (allChecked) {
                selectAllCheckbox.checked = true;
            }
        });
    });
});

document.getElementById('select-all').addEventListener('change', function(e) {
            const checkboxes = document.querySelectorAll('.client-checkbox');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = e.target.checked;
            });
        });

// Update button label and hidden input on selection
document.querySelectorAll('#priorityDropdown ~ .dropdown-menu .dropdown-item').forEach(item => {
    item.addEventListener('click', function (e) {
        e.preventDefault();
        const value = this.dataset.value;
        const label = this.textContent;
        document.getElementById('priorityDropdown').textContent = label;
        document.getElementById('id_priority').value = value;
    });
});

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
});






