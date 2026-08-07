document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('contact-search-input');
    const list  = document.getElementById('contact-autocomplete-list');
    if (!input || !list) return;

    const autocompleteUrl = input.dataset.autocompleteUrl;
    const listBase = input.dataset.listUrl;
    let activeIndex = -1;
    let suggestions = [];

    function closeList() {
        list.innerHTML = '';
        list.style.display = 'none';
        activeIndex = -1;
    }

    function goToContact(item) {
        window.location.href = listBase + '?id=' + item.id;
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
                            goToContact(item);
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
                goToContact(suggestions[activeIndex]);
            } else if (e.key === 'Escape') {
                closeList();
            }
        });

        document.addEventListener('click', function (e) {
            if (!list.contains(e.target) && e.target !== input) closeList();
        });


});

