/**
 * Purchase Chart Module
 * Handles the interactive product purchase chart using Plotly.js
 */

(function() {
    'use strict';

    // Store chart data globally within this module
    let purchaseChartData = null;

    const colors = [
        '#0d6efd', '#198754', '#dc3545', '#ffc107',
        '#6f42c1', '#fd7e14', '#20c997', '#0dcaf0',
        '#d63384', '#6610f2', '#9fc4f3', '#4e886b', '#ebec3d', '#c3e748'
    ];

    const FONT_FAMILY = 'Arial, sans-serif';
    let hasChartData = false;

    /**
     * Width of a chart container (falls back to the viewport width)
     */
    function getContainerWidth(divId) {
        const el = document.getElementById(divId);
        return (el && el.clientWidth) ? el.clientWidth : window.innerWidth;
    }

    /**
     * Responsive sizes based on the container width.
     * compact = legend goes below the chart instead of to the right.
     */
    function getResponsiveSizes(width) {
        if (width < 480) {
            return { title: 14, base: 10, axis: 11, legend: 10, maxLabel: 18, compact: true };
        }
        if (width < 768) {
            return { title: 16, base: 11, axis: 12, legend: 11, maxLabel: 24, compact: true };
        }
        return { title: 18, base: 12, axis: 14, legend: 12, maxLabel: 28, compact: false };
    }

    /**
     * Escape characters that Plotly's pseudo-HTML would interpret
     */
    function escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    /**
     * Reverse of escapeHtml – legend DOM text is shown unescaped
     */
    function unescapeHtml(text) {
        return String(text)
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&');
    }

    /**
     * Show the full product name as a native tooltip when hovering
     * a shortened ("…") legend item. Plotly has no legend tooltips,
     * so we add an SVG <title> to each legend entry after every redraw.
     */
    function attachLegendTooltips(divId) {
        const gd = document.getElementById(divId);
        if (!gd || !gd.data) return;

        const applyTooltips = function() {
            // Map: displayed (short) label -> full name
            const fullNames = {};
            (gd.data || []).forEach(function(trace) {
                if (trace.type === 'pie') {
                    (trace.labels || []).forEach(function(label, i) {
                        const full = trace.customdata && trace.customdata[i];
                        if (full) fullNames[unescapeHtml(label)] = unescapeHtml(full);
                    });
                } else if (trace.name && trace.meta) {
                    fullNames[unescapeHtml(trace.name)] = unescapeHtml(trace.meta);
                }
            });

            gd.querySelectorAll('.legend .traces').forEach(function(item) {
                const textEl = item.querySelector('.legendtext');
                if (!textEl) return;
                const shown = textEl.textContent;
                const full = fullNames[shown];

                const old = item.querySelector(':scope > title');
                if (old) old.remove();
                if (!full || full === shown) return;

                const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
                title.textContent = full;
                item.insertBefore(title, item.firstChild);
            });
        };

        // Legend is rebuilt on every redraw/toggle, so re-apply each time
        if (!gd._legendTooltipsBound && typeof gd.on === 'function') {
            gd.on('plotly_afterplot', applyTooltips);
            gd._legendTooltipsBound = true;
        }
        applyTooltips();
    }

    /**
     * Shorten a long label with an ellipsis (full name is kept for hover)
     */
    function shortenLabel(text, maxLength) {
        const str = String(text);
        return str.length > maxLength ? str.slice(0, maxLength - 1).trimEnd() + '…' : str;
    }

    /**
     * Shorten labels and keep them unique (pie charts merge identical labels)
     */
    function shortenUniqueLabels(names, maxLength) {
        const seen = {};
        return names.map(function(name) {
            let label = escapeHtml(shortenLabel(name, maxLength));
            if (seen[label]) {
                seen[label] += 1;
                label = label + ' (' + seen[label] + ')';
            } else {
                seen[label] = 1;
            }
            return label;
        });
    }

    /**
     * Legend settings: right side on wide screens, horizontal below on narrow ones
     */
    function createLegend(sizes) {
        const base = {
            bgcolor: 'rgba(255,255,255,0.9)',
            bordercolor: '#ddd',
            borderwidth: 1,
            font: { size: sizes.legend }
        };
        if (sizes.compact) {
            return Object.assign(base, { orientation: 'h', x: 0, xanchor: 'left', y: -0.15, yanchor: 'top' });
        }
        return Object.assign(base, { orientation: 'v', x: 1.02, xanchor: 'left', y: 1, yanchor: 'top' });
    }

    /**
     * Debounce helper for the resize handler
     */
    function debounce(fn, wait) {
        let timer = null;
        return function() {
            clearTimeout(timer);
            timer = setTimeout(fn, wait);
        };
    }

    /**
     * Initialize the purchase chart
     */
    function initPurchaseChart(data) {
        purchaseChartData = data || {};

        attachEventListeners();

        // Check if there's any data in either currency
        const hasEurData = purchaseChartData.products_eur && Object.keys(purchaseChartData.products_eur).length > 0;
        const hasUsdData = purchaseChartData.products_usd && Object.keys(purchaseChartData.products_usd).length > 0;
        const hasTotalData = purchaseChartData.products_total && Object.keys(purchaseChartData.products_total).length > 0;

        if (!hasEurData && !hasUsdData && !hasTotalData) {
            showNoDataMessage();
            renderEmptyPieMessages();
            return;
        }
        hasChartData = true;

        // Initialize displays with current filter values
        const currencySelect = document.getElementById('purchaseCurrency');
        const dataTypeSelect = document.getElementById('purchaseDataType');
        const currentCurrency = currencySelect ? currencySelect.value : 'EUR';
        const currentDataType = dataTypeSelect ? dataTypeSelect.value : 'quantity';

        updateRevenueDisplay(currentCurrency, currentDataType);
        renderPurchaseChart();
        renderStatsPies();
    }

    function renderEmptyPieMessages() {
        ['purchasePieQuantity', 'purchasePieRevenue'].forEach(function(id) {
            const div = document.getElementById(id);
            if (div) {
                div.innerHTML =
                    '<div class="alert alert-info text-center my-5" role="alert">' +
                    'No purchase data available.' +
                    '</div>';
            }
        });
    }

        /**
     * Render two fixed pie charts: total products sold and total revenue in EUR
     */
    function renderStatsPies() {
        const products = purchaseChartData.products_total;
        if (!products || Object.keys(products).length === 0) return;

        const names = Object.keys(products);
        const quantities = [];
        const revenues = [];

        names.forEach(function(productName) {
            const d = products[productName];
            quantities.push((d.quantities || []).reduce(function(a, b) { return a + b; }, 0));
            revenues.push((d.amounts_eur_total || []).reduce(function(a, b) { return a + b; }, 0));
        });

        renderPie('purchasePieQuantity', names, quantities, 'Total Products Sold',
            '<b>%{customdata}</b><br>Qty: %{value:,}<br>Share: %{percent}<extra></extra>');
        renderPie('purchasePieRevenue', names, revenues, 'Total Revenue (all in EUR)',
            '<b>%{customdata}</b><br>Revenue: €%{value:,.2f}<br>Share: %{percent}<extra></extra>');
    }

    /**
     * Render one responsive pie chart
     */
    function renderPie(divId, names, values, title, hoverTemplate) {
        const div = document.getElementById(divId);
        if (!div) return;

        const sizes = getResponsiveSizes(getContainerWidth(divId));
        // Pies sit in half-width columns, so shorten labels a bit more
        const labels = shortenUniqueLabels(names, Math.max(14, sizes.maxLabel - 6));

        // Horizontal legend below needs extra height, one row per ~2 items
        const height = sizes.compact ? 340 + Math.ceil(names.length / 2) * 22 : 380;
        div.style.height = height + 'px';

        Plotly.react(divId, [{
            type: 'pie',
            labels: labels,
            values: values,
            customdata: names.map(escapeHtml),
            marker: { colors: colors },
            hovertemplate: hoverTemplate,
            // Only percentages on slices – names live in the legend/tooltip
            textinfo: 'percent',
            textposition: 'inside',
            insidetextorientation: 'horizontal',
            sort: true
        }], {
            title: { text: title, font: { size: sizes.title - 2, family: FONT_FAMILY, color: '#333' } },
            showlegend: true,
            legend: createLegend(sizes),
            uniformtext: { minsize: 9, mode: 'hide' },
            margin: { t: 50, r: 10, b: 10, l: 10 },
            height: height,
            paper_bgcolor: 'rgb(250,250,248)',
            font: { family: FONT_FAMILY, size: sizes.base, color: '#333' }
        }, { responsive: true, displayModeBar: false }).then(function() {
            attachLegendTooltips(divId);
        });
    }

    /**
     * Render the purchase chart
     */
    function renderPurchaseChart() {
        const chartDiv = document.getElementById('purchaseChart');
        const chartTypeSelect = document.getElementById('purchaseChartType');
        const dataTypeSelect = document.getElementById('purchaseDataType');
        const currencySelect = document.getElementById('purchaseCurrency');

         if (!chartDiv || !chartTypeSelect || !dataTypeSelect || !currencySelect) {
            return;
        }

         const chartType = chartTypeSelect.value;
        const dataType = dataTypeSelect.value;
        const currency = currencySelect.value;

        const sizes = getResponsiveSizes(getContainerWidth('purchaseChart'));
        const traces = createTraces(chartType, dataType, currency, sizes);
        const layout = createLayout(dataType, currency, chartType, sizes, traces);
        const config = createConfig();

        Plotly.react('purchaseChart', traces, layout, config).then(function() {
            attachLegendTooltips('purchaseChart');
        });
    }

    /**
     * Create chart traces for each product
     */
    function createTraces(chartType, dataType, currency, sizes) {
        // Select the correct product data based on data type and currency
        let products = {};
        if (dataType === 'total_products' || dataType === 'total_revenue') {
            products = purchaseChartData.products_total || {};
        } else {
            products = currency === 'EUR' ? (purchaseChartData.products_eur || {})  :( purchaseChartData.products_usd || {});
        }

        if (Object.keys(products).length === 0) {
            return [{
                x: [],
                y: [],
                name: 'No data',
                type: chartType === 'scatter' ? 'scatter' : 'bar',
                mode: chartType === 'scatter' ? 'markers' : undefined
            }];
        }

        if (chartType === 'pie') {
            const names = [];
            const values = [];

            Object.keys(products).forEach(productName => {
                const productData = products[productName];
                let total;
                if (dataType === 'quantity' || dataType === 'total_products') {
                    total = (productData.quantities || []).reduce(function (a,b){return a + b;}, 0);
                } else if (dataType === 'total_revenue') {
                    const arr = currency === 'EUR' ? (productData.amounts_eur_total || []) : (productData.amounts_usd_total || []);
                    total = arr.reduce(function (a, b) {return a + b;}, 0);
                } else {
                    total = (productData.amounts || []).reduce(function (a, b){return a + b;}, 0);
                }
                names.push(productName);
                values.push(total);
            });

            const currencySymbol = currency === 'EUR' ? '€' : '$';
            const isAmount = dataType === 'amount' || dataType === 'total_revenue';
            const hoverTemplate = isAmount
                ? '<b>%{customdata}</b><br>Value: ' + currencySymbol + '%{value:,.2f}<br>Share: %{percent}<extra></extra>'
                : '<b>%{customdata}</b><br>Value: %{value:,}<br>Share: %{percent}<extra></extra>';

            return [{
                type: 'pie',
                labels: shortenUniqueLabels(names, sizes.maxLabel),
                values: values,
                customdata: names.map(escapeHtml),
                marker: { colors: colors },
                hovertemplate: hoverTemplate,
                textinfo: 'percent',
                textposition: 'inside',
                insidetextorientation: 'horizontal',
                hole: 0
            }];
        }

        if (chartType === 'scatter') {
            const currencySymbol = currency === 'EUR' ? '€' : '$';
            const traces = [];
            let colorIndex = 0;

            Object.keys(products).forEach(productName => {
                const productData = products[productName];

                let amounts;
                if (dataType === 'total_revenue') {
                    amounts = currency === 'EUR'
                        ? (productData.amounts_eur_total || [])
                        : (productData.amounts_usd_total || []);
                } else if (dataType === 'amount') {
                    amounts = productData.amounts || [];
                } else {
                    amounts = productData.quantities || [];
                }

                traces.push({
                    x: productData.quantities || [],
                    y: amounts,
                    name: escapeHtml(shortenLabel(productName, sizes.maxLabel)),
                    meta: escapeHtml(productName),
                    type: 'scatter',
                    mode: 'markers',
                    marker: {
                        color: colors[colorIndex % colors.length],
                        size: sizes.compact ? 8 : 10,
                        opacity: 0.8,
                        line: { color: 'white', width: 1 }
                    },
                    hovertemplate: '<b>%{meta}</b><br>Quantity: %{x}<br>Price: ' + currencySymbol + '%{y:,.2f}<extra></extra>'
                });

                colorIndex++;
            });

            return traces;
        }

        const traces = [];
        let colorIndex = 0;

        Object.keys(products).forEach(productName => {
            const productData = products[productName];

            let yData = [];

            if (dataType === 'quantity' || dataType === 'total_products') {
                yData = productData.quantities || [];
            } else if (dataType === 'total_revenue') {
                yData = currency === 'EUR'
                    ? (productData.amounts_eur_total || [])
                    : (productData.amounts_usd_total || []);
            } else {
                yData = productData.amounts || [];
            }

            traces.push({
                x: productData.dates || [],
                y: yData,
                name: escapeHtml(shortenLabel(productName, sizes.maxLabel)),
                meta: escapeHtml(productName),
                type: 'bar',
                marker: { color: colors[colorIndex % colors.length] },
                hovertemplate: createHoverTemplate(dataType, currency)
            });

            colorIndex++;
        });

        return traces;
    }

    /**
     * Create hover template
     */
    function createHoverTemplate(dataType, currency) {
        const currencySymbol = currency === 'EUR' ? '€' : '$';

        if (dataType === 'quantity') {
            return '<b>%{meta}</b><br>' +
                   'Date: %{x|%Y-%m-%d}<br>' +
                   'Quantity: %{y}<br>' +
                   '<extra></extra>';
        } else if (dataType === 'total_products') {
            return '<b>%{meta}</b><br>' +
                   'Date: %{x|%Y-%m-%d}<br>' +
                   'Total Products Sold: %{y}<br>' +
                   '<extra></extra>';
        } else if (dataType === 'amount') {
            return '<b>%{meta}</b><br>' +
                   'Date: %{x|%Y-%m-%d}<br>' +
                   'Amount: ' + currencySymbol + '%{y:,.2f}<br>' +
                   '<extra></extra>';
        } else if (dataType === 'total_revenue') {
            return '<b>%{meta}</b><br>' +
                   'Date: %{x|%Y-%m-%d}<br>' +
                   'Total Revenue: ' + currencySymbol + '%{y:,.2f}<br>' +
                   '<extra></extra>';
        } else {
            return '<b>%{meta}</b><br>' +
                   'Date: %{x|%Y-%m-%d}<br>' +
                   'Value: %{y}<br>' +
                   '<extra></extra>';
        }
    }

    /**
     * Create chart layout
     */
    function createLayout(dataType, currency, chartType, sizes, traces) {
        let chartTitle;
        if (dataType === 'quantity') chartTitle = 'Product Purchases (Quantity)';
        else if (dataType === 'total_products') chartTitle = 'Total Products Sold';
        else if (dataType === 'amount') chartTitle = 'Product Purchases (Revenue)';
        else if (dataType === 'total_revenue') chartTitle = 'Total Revenue';
        else chartTitle = 'Product Purchases';

        // Number of legend entries (pie has one trace with many labels)
        const legendItems = chartType === 'pie'
            ? ((traces[0] && traces[0].labels) ? traces[0].labels.length : 0)
            : traces.length;
        // Below-chart legend needs extra height so it doesn't squash the plot
        const height = sizes.compact ? 420 + Math.ceil(legendItems / 2) * 22 : 500;

        const common = {
            title: {
                text: chartTitle,
                font: { size: sizes.title, family: FONT_FAMILY, color: '#333' },
                automargin: true
            },
            showlegend: true,
            legend: createLegend(sizes),
            height: height,
            plot_bgcolor: 'rgba(255,255,255,1)',
            paper_bgcolor: 'rgb(250,250,248)',
            font: { family: FONT_FAMILY, size: sizes.base, color: '#333' }
        };

        if (chartType === 'pie') {
            return Object.assign(common, {
                uniformtext: { minsize: 9, mode: 'hide' },
                margin: { t: 60, r: 20, b: 20, l: 20 }
            });
        }

        const currencySymbol = currency === 'EUR' ? '€' : '$';
        // Right margin is small: Plotly auto-expands it to fit the legend
        const margin = sizes.compact
            ? { t: 50, r: 10, b: 20, l: 10 }
            : { t: 60, r: 20, b: 60, l: 20 };

        const axisBase = {
            gridcolor: '#e5e5e5',
            showgrid: true,
            zeroline: false,
            automargin: true,
            tickfont: { size: sizes.base }
        };

        if (chartType === 'scatter') {
            common.title.text = 'Quantity vs Price';
            return Object.assign(common, {
                xaxis: Object.assign({}, axisBase, {
                    title: { text: 'Quantity', font: { size: sizes.axis, color: '#666' } },
                    tickformat: ','
                }),
                yaxis: Object.assign({}, axisBase, {
                    title: { text: 'Price (' + currencySymbol + ')', font: { size: sizes.axis, color: '#666' } },
                    tickformat: ',.2f',
                    tickprefix: currencySymbol
                }),
                hovermode: 'closest',
                margin: margin
            });
        }

        let yAxisTitle, tickFormat, tickPrefix;

        if (dataType === 'quantity' || dataType === 'total_products') {
            yAxisTitle = dataType === 'quantity' ? 'Quantity Sold' : 'Total Products Sold';
            tickFormat = ',';
            tickPrefix = '';
        } else {
            yAxisTitle = (dataType === 'total_revenue' ? 'Total Revenue' : 'Revenue') + ' (' + currencySymbol + ')';
            tickFormat = ',.2f';
            tickPrefix = currencySymbol;
        }

        return Object.assign(common, {
            xaxis: Object.assign({}, axisBase, {
                // On narrow screens drop the "Date" title to leave room for the legend
                title: sizes.compact ? undefined : { text: 'Date', font: { size: sizes.axis, color: '#666' } },
                type: 'date',
                tickformat: '%Y-%m-%d',
                nticks: sizes.compact ? 4 : undefined
            }),
            yaxis: Object.assign({}, axisBase, {
                title: { text: yAxisTitle, font: { size: sizes.axis, color: '#666' } },
                tickformat: tickFormat,
                tickprefix: tickPrefix
            }),
            hovermode: 'closest',
            margin: margin
        });
    }

    /**
     * Create chart configuration
     */
    function createConfig() {
        return {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            scrollZoom: true,
            toImageButtonOptions: {
                format: 'png',
                filename: 'purchase_chart_' + new Date().toISOString().split('T')[0],
                height: 600,
                width: 1200,
                scale: 2
            }
        };
    }

    /**
     * Show no data message
     */
    function showNoDataMessage() {
        const chartDiv = document.getElementById('purchaseChart');
        if (chartDiv) {
            chartDiv.innerHTML =
                '<div class="alert alert-info text-center my-5" role="alert">' +
                '<i class="bi bi-info-circle fs-1"></i>' +
                '<p class="mt-3 mb-0 fs-5">No purchase data available for the selected filters.</p>' +
                '<p class="text-muted">Try adjusting your filter selections or add some purchases.</p>' +
                '</div>';
        }
    }

    /**
     * Update total revenue and items display based on selected currency and data type
     */
    function updateRevenueDisplay(currency, dataType) {
        const revenueDisplay = document.getElementById('totalRevenueDisplay');
        const itemsDisplay = document.getElementById('totalItemsDisplay');

        // Hide both if total_revenue is selected
        if (dataType === 'total_revenue') {
            if (revenueDisplay) {
                revenueDisplay.textContent = '—';
            }
            if (itemsDisplay) {
                itemsDisplay.textContent = '—';
            }
            return;
        }
        if (dataType === 'total_products') {
            if (revenueDisplay) {
                revenueDisplay.textContent = '—';
            }
            if (itemsDisplay) {
                itemsDisplay.textContent = '—';
            }
            return;
        }

        // Update revenue display based on currency
        if (revenueDisplay) {
            const eurRevenue = parseFloat(revenueDisplay.dataset.eur);
            const usdRevenue = parseFloat(revenueDisplay.dataset.usd);

            if (currency === 'EUR') {
                revenueDisplay.textContent = '€' + eurRevenue.toFixed(2);
            } else {
                revenueDisplay.textContent = '$' + usdRevenue.toFixed(2);
            }
        }

        // Update items display based on currency
        if (itemsDisplay) {
            const eurItems = parseInt(itemsDisplay.dataset.eur);
            const usdItems = parseInt(itemsDisplay.dataset.usd);

            if (currency === 'EUR') {
                itemsDisplay.textContent = eurItems;
            } else {
                itemsDisplay.textContent = usdItems;
            }
        }
    }

    /**
     * Attach event listeners to filter controls
     */
    function attachEventListeners() {
        // Update chart without page reload
        const chartTypeSelect = document.getElementById('purchaseChartType');
        const dataTypeSelect = document.getElementById('purchaseDataType');
        const currencySelect = document.getElementById('purchaseCurrency');

        if (chartTypeSelect) {
            chartTypeSelect.addEventListener('change', renderPurchaseChart);
        }

        if (dataTypeSelect) {
            dataTypeSelect.addEventListener('change', function() {
                const currency = currencySelect ? currencySelect.value : 'EUR';
                updateRevenueDisplay(currency, this.value);
                renderPurchaseChart();
            });
        }

        if (currencySelect) {
            currencySelect.addEventListener('change', function() {
                const dataType = dataTypeSelect ? dataTypeSelect.value : 'quantity';
                updateRevenueDisplay(this.value, dataType);
                renderPurchaseChart();
            });
        }

        // Reload page for product and period changes
        const productSelect = document.getElementById('purchaseProduct');
        const periodSelect = document.getElementById('purchasePeriod');

        if (productSelect) {
            productSelect.addEventListener('change', function() {
                updateURLParameter('purchase_product', this.value);
            });
        }

        if (periodSelect) {
            periodSelect.addEventListener('change', function() {
                updateURLParameter('purchase_period', this.value);
            });
        }
    }

    /**
     * Update URL parameter and reload
     */
    function updateURLParameter(param, value) {
        const url = new URL(window.location);
        url.searchParams.set(param, value);
        window.location.href = url.toString();
    }

    /**
     * Initialize when DOM is ready
     */
    document.addEventListener('DOMContentLoaded', function() {
        // Check if purchase chart data exists (injected from Django template)
        if (typeof window.purchaseChartData !== 'undefined') {
            initPurchaseChart(window.purchaseChartData);
        }
    });

    // Re-render on resize so font sizes, label length and legend position adapt
    window.addEventListener('resize', debounce(function() {
        if (!hasChartData) return;
        renderPurchaseChart();
        renderStatsPies();
    }, 250));

    // Expose init function globally if needed
    window.initPurchaseChart = initPurchaseChart;

})();