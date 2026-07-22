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

document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('client-search');
    const list = document.getElementById('client-autocomplete-list');

    if (!input || !list) {
        return;
    }

    const autocompleteUrl = input.dataset.autocompleteUrl;
    const detailBase = input.dataset.detailBase.replace(/\/$/, '');

    let activeIndex = -1;
    let suggestions = [];

    function closeList() {
        list.innerHTML = '';
        list.style.display = 'none';
        activeIndex = -1;
    }

    function goToClient(item) {
        window.location.href = detailBase + '/' + item.id + '/';
    }

    function setActive(items) {
        items.forEach((el, i) => {
            el.classList.toggle('active', i === activeIndex);
        });
    }

    input.addEventListener('input', function () {
        const q = this.value.trim();

        closeList();
        suggestions = [];

        if (!q) {
            return;
        }

        fetch(`${autocompleteUrl}?q=${encodeURIComponent(q)}`)
            .then((response) => response.json())
            .then((data) => {
                if (!data.length) {
                    return;
                }

                suggestions = data;

                data.forEach((item, idx) => {
                    const li = document.createElement('li');

                    li.className = 'list-group-item list-group-item-action';
                    li.style.cursor = 'pointer';
                    li.textContent = item.label;
                    li.dataset.index = idx;

                    li.addEventListener('mousedown', function (e) {
                        e.preventDefault();
                        goToClient(item);
                    });

                    list.appendChild(li);
                });

                list.style.display = 'block';
                activeIndex = -1;
            });
    });

    input.addEventListener('keydown', function (e) {
        const items = [...list.querySelectorAll('li')];

        if (!items.length) {
            return;
        }

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = Math.min(activeIndex + 1, items.length - 1);
            setActive(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = Math.max(activeIndex - 1, 0);
            setActive(items);
        } else if (e.key === 'Enter' && activeIndex >= 0) {
            e.preventDefault();
            goToClient(suggestions[activeIndex]);
        } else if (e.key === 'Escape') {
            closeList();
        }
    });

    document.addEventListener('click', function (e) {
        if (!list.contains(e.target) && e.target !== input) {
            closeList();
        }
    });
});






