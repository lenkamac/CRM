document.addEventListener('DOMContentLoaded', function () {

    // Auto-dismiss alerts after 3 seconds
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (alert) {
            alert.style.transition = 'opacity 0.5s linear';
            alert.style.opacity = 0;
            setTimeout(function () { alert.remove(); }, 500);
        });
    }, 3000);

    // Currency conversion
    const EUR_TO_USD = 1.08;

    document.querySelectorAll('.currency-toggle').forEach(function (button) {
        button.addEventListener('click', function () {
            const currency = this.dataset.currency;

            document.querySelectorAll('.currency-toggle').forEach(function (btn) {
                btn.classList.remove('active');
            });
            this.classList.add('active');

            document.querySelectorAll('.price-cell').forEach(function (cell) {
                const eurPrice = parseFloat(cell.dataset.eur);
                const symbol = cell.querySelector('.currency-symbol');
                const valueSpan = cell.querySelector('.price-value');

                if (currency === 'USD') {
                    symbol.textContent = '$';
                    valueSpan.textContent = (eurPrice * EUR_TO_USD).toFixed(2);
                } else {
                    symbol.textContent = '€';
                    valueSpan.textContent = eurPrice.toFixed(2);
                }
            });
        });
    });

    // Product search autocomplete
    const input = document.getElementById('product-search');
    if (!input) return;

    const list = document.getElementById('product-autocomplete-list');
    const searchBtn = document.getElementById('product-search-btn');
    const autocompleteUrl = input.dataset.autocompleteUrl;
    const detailBase = input.dataset.detailBaseUrl.replace(/\/$/, '');
    let activeIndex = -1;
    let suggestions = [];

    function closeList() {
        list.innerHTML = '';
        list.style.display = 'none';
        activeIndex = -1;
    }

    function goToProduct(item) {
        window.location.href = detailBase + '/' + item.id + '/';
    }

    function setActive(items) {
        items.forEach(function (el, i) {
            el.classList.toggle('active', i === activeIndex);
        });
    }

    function fetchSuggestions(q) {
        closeList();
        suggestions = [];
        if (!q) return;

        fetch(autocompleteUrl + '?q=' + encodeURIComponent(q))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.length) return;
                suggestions = data;
                data.forEach(function (item) {
                    const li = document.createElement('li');
                    li.className = 'list-group-item list-group-item-action';
                    li.style.cursor = 'pointer';
                    li.textContent = item.label;
                    li.addEventListener('mousedown', function (e) {
                        e.preventDefault();
                        goToProduct(item);
                    });
                    list.appendChild(li);
                });
                list.style.display = 'block';
                activeIndex = -1;
            });
    }

    input.addEventListener('input', function () {
        fetchSuggestions(this.value.trim());
    });

    searchBtn.addEventListener('click', function () {
        const q = input.value.trim();
        if (suggestions.length === 1) {
            goToProduct(suggestions[0]);
        } else if (activeIndex >= 0 && suggestions[activeIndex]) {
            goToProduct(suggestions[activeIndex]);
        } else {
            fetchSuggestions(q);
        }
    });

    input.addEventListener('keydown', function (e) {
        const items = [...list.querySelectorAll('li')];
        if (e.key === 'Enter') {
            e.preventDefault();
            if (activeIndex >= 0 && suggestions[activeIndex]) {
                goToProduct(suggestions[activeIndex]);
            } else if (suggestions.length === 1) {
                goToProduct(suggestions[0]);
            } else {
                fetchSuggestions(this.value.trim());
            }
            return;
        }
        if (!items.length) return;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = Math.min(activeIndex + 1, items.length - 1);
            setActive(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = Math.max(activeIndex - 1, 0);
            setActive(items);
        } else if (e.key === 'Escape') {
            closeList();
        }
    });

    document.addEventListener('click', function (e) {
        if (!list.contains(e.target) && e.target !== input && e.target !== searchBtn) {
            closeList();
        }
    });
});
