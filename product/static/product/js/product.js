document.addEventListener('DOMContentLoaded', function () {

    // Currency conversion
    let eurToUsdRate = null;

    function getExchangeRateUrl() {
        const rateContainer = document.querySelector('[data-exchange-rate-url]');
        return rateContainer ? rateContainer.dataset.exchangeRateUrl : null;
    }

    function fetchExchangeRate() {
        const exchangeRateUrl = getExchangeRateUrl();

        if (!exchangeRateUrl) {
            return Promise.resolve(1.10);
        }

        if (eurToUsdRate !== null) {
            return Promise.resolve(eurToUsdRate);
        }

        return fetch(exchangeRateUrl)
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('Exchange rate request failed');
                }
                return response.json();
            })
            .then(function (data) {
                eurToUsdRate = parseFloat(data.rate);
                return eurToUsdRate;
            })
            .catch(function () {
                eurToUsdRate = 1.10;
                return eurToUsdRate;
            });
    }

    function updatePriceCells(currency, exchangeRate) {
        document.querySelectorAll('.price-cell').forEach(function (cell) {
            const symbol = cell.querySelector('.currency-symbol');
            const priceValue = cell.querySelector('.price-value');
            const eurPrice = parseFloat(cell.dataset.eur);

            if (!symbol || !priceValue || Number.isNaN(eurPrice)) {
                return;
            }

            if (currency === 'USD') {
                const usdPrice = eurPrice * exchangeRate;

                symbol.textContent = '$';

                if (cell.classList.contains('total-cell')) {
                    const quantity = parseInt(cell.dataset.quantity, 10) || 1;
                    priceValue.textContent = (usdPrice * quantity).toFixed(2);
                } else {
                    priceValue.textContent = usdPrice.toFixed(2);
                }
            } else {
                symbol.textContent = '€';

                if (cell.classList.contains('total-cell')) {
                    const quantity = parseInt(cell.dataset.quantity, 10) || 1;
                    priceValue.textContent = (eurPrice * quantity).toFixed(2);
                } else {
                    priceValue.textContent = eurPrice.toFixed(2);
                }
            }
        });
    }

    document.querySelectorAll('.currency-toggle').forEach(function (button) {
        button.addEventListener('click', function () {
            const currency = this.dataset.currency;

            document.querySelectorAll('.currency-toggle').forEach(function (btn){
                btn.classList.remove('active');
            })
            this.classList.add('active');

            fetchExchangeRate().then(function (ExchangeRate){
                updatePriceCells(currency, ExchangeRate);
            });
        });
    });

    // Purchase search autocomplete
    const purchaseInput = document.getElementById('purchase_search');
    const purchaseList = document.getElementById('purchase_autocomplete_list');

    if (purchaseInput && purchaseList) {
        const purchaseAutocompleteUrl = purchaseInput.dataset.autocompleteUrl;
        let purchaseActiveIndex = -1;
        let purchaseSuggestions = [];

        function closePurchaseList() {
            purchaseList.innerHTML = '';
            purchaseList.style.display = 'none';
            purchaseActiveIndex = -1;
        }

        function setActivePurchaseItem(items) {
            items.forEach(function (el, i) {
                el.classList.toggle('active', i === purchaseActiveIndex);
            });
        }

        function fetchPurchaseSuggestions(q) {
            closePurchaseList();
            purchaseSuggestions = [];

            if (!q) {
                return;
            }

            fetch(purchaseAutocompleteUrl + '?q=' + encodeURIComponent(q))
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    if (!data.length) {
                        return;
                    }

                    purchaseSuggestions = data;

                    data.forEach(function (item) {
                        const li = document.createElement('li');
                        li.className = 'list-group-item list-group-item-action';
                        li.style.cursor = 'pointer';
                        li.textContent = item.label;

                        li.addEventListener('mousedown', function (event) {
                            event.preventDefault();
                            purchaseInput.value = item.label;
                            closePurchaseList();
                            purchaseInput.form.submit();
                        });

                        purchaseList.appendChild(li);
                    });

                    purchaseList.style.display = 'block';
                    purchaseActiveIndex = -1;
                });
        }

        purchaseInput.addEventListener('input', function () {
            fetchPurchaseSuggestions(this.value.trim());
        });

        purchaseInput.addEventListener('keydown', function (event) {
            const items = [...purchaseList.querySelectorAll('li')];

            if (event.key === 'Enter') {
                if (purchaseActiveIndex >= 0 && purchaseSuggestions[purchaseActiveIndex]) {
                    event.preventDefault();
                    purchaseInput.value = purchaseSuggestions[purchaseActiveIndex].label;
                    closePurchaseList();
                    purchaseInput.form.submit();
                }
                return;
            }

            if (!items.length) {
                return;
            }

            if (event.key === 'ArrowDown') {
                event.preventDefault();
                purchaseActiveIndex = Math.min(purchaseActiveIndex + 1, items.length - 1);
                setActivePurchaseItem(items);
            } else if (event.key === 'ArrowUp') {
                event.preventDefault();
                purchaseActiveIndex = Math.max(purchaseActiveIndex - 1, 0);
                setActivePurchaseItem(items);
            } else if (event.key === 'Escape') {
                closePurchaseList();
            }
        });

        document.addEventListener('click', function (event) {
            if (!purchaseList.contains(event.target) && event.target !== purchaseInput) {
                closePurchaseList();
            }
        });
    }

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

document.addEventListener('DOMContentLoaded', function () {
            if (typeof flatpickr !== 'undefined') {
                flatpickr('#purchase_date_from', {
                    dateFormat: 'd.m.Y',
                    allowInput: true,
                    static: true,
                    locale: {
                        firstDayOfWeek: 1
                    }
                });

                flatpickr('#purchase_date_to', {
                    dateFormat: 'd.m.Y',
                    allowInput: true,
                    static: true,
                    locale: {
                        firstDayOfWeek: 1
                    }
                });
            }
        });