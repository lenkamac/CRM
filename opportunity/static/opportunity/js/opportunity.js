document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select-all');
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = selectAllCheckbox;
            rowCheckboxes.forEach((checkbox) => {
                checkbox.checked = isChecked;
            });
        });

        rowCheckboxes.forEach((checkbox) => {
            checkbox.addEventListener('change', function () {
                if (!checkbox.checked) {
                    selectAllCheckbox.checked = false;
                }
            });
        });

        rowCheckboxes.forEach((checkbox) => {
            checkbox.addEventListener('change', function () {
                const allChecked = Array.from(rowCheckboxes).every((cb) => cb.checked);
                if (allChecked) {
                    selectAllCheckbox.checked = true;
                }
            });
        });

        selectAllCheckbox.addEventListener('change', function (e) {
            const checkboxes = document.querySelectorAll('.opportunity-checkbox');
            checkboxes.forEach(function (checkbox) {
                checkbox.checked = e.target.checked;
            });
        });
    }

    document.querySelectorAll('#priorityDropdown ~ .dropdown-menu .dropdown-item').forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const value = this.dataset.value;
            const label = this.textContent;
            document.getElementById('priorityDropdown').textContent = label;
            document.getElementById('id_priority').value = value;
        });
    });

    document.querySelectorAll('#statusDropdown ~ .dropdown-menu .dropdown-item').forEach(function (item) {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            document.getElementById('statusDropdown').textContent = this.textContent;
            document.getElementById('id_status').value = this.dataset.value;
        });
    });

})