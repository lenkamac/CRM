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
            const checkboxes = document.querySelectorAll('.lead-checkbox');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = e.target.checked;
            });
        });

(function () {
    const input = document.getElementById('lead-search');
    if (!input) return;
    const list = document.getElementById('lead-autocomplete-list');
    const autocompleteUrl = input.dataset.autocompleteUrl;
    const detailBase = input.dataset.listUrl.replace(/\/$/, '');
    let activeIndex = -1;
    let suggestions = [];

    function closeList() {
        list.innerHTML = '';
        list.style.display = 'none';
        activeIndex = -1;
    }

    function goToLead(item) {
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
        if (!q) return;

        fetch(`${autocompleteUrl}?q=${encodeURIComponent(q)}`)
            .then(r => r.json())
            .then(data => {
                if (!data.length) return;
                suggestions = data;
                data.forEach((item, idx) => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item list-group-item-action';
                    li.style.cursor = 'pointer';
                    li.textContent = item.label;
                    li.dataset.index = idx;
                    li.addEventListener('mousedown', function (e) {
                        e.preventDefault();
                        goToLead(item);
                    });
                    list.appendChild(li);
                });
                list.style.display = 'block';
                activeIndex = -1;
            });
    });

    input.addEventListener('keydown', function (e) {
        const items = [...list.querySelectorAll('li')];
        if (!items.length) return;
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
            goToLead(suggestions[activeIndex]);
        } else if (e.key === 'Escape') {
            closeList();
        }
    });

    document.addEventListener('click', function (e) {
        if (!list.contains(e.target) && e.target !== input) closeList();
    });
})();
