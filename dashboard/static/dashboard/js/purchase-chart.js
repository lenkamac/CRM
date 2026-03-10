/**
 * Purchase Chart Module
 * Handles the interactive product purchase chart using Plotly.js
 */

(function() {
    'use strict';

    // Store chart data globally within this module
    let purchaseChartData = null;

    /**
     * Initialize the purchase chart
     */
    function initPurchaseChart(data) {
        purchaseChartData = data;

        // Check if there's any data in either currency
        const hasEurData = purchaseChartData.products_eur && Object.keys(purchaseChartData.products_eur).length > 0;
        const hasUsdData = purchaseChartData.products_usd && Object.keys(purchaseChartData.products_usd).length > 0;

        if (!purchaseChartData || (!hasEurData && !hasUsdData)) {
            showNoDataMessage();
            return;
        }

        // Initialize displays with current filter values
        const currencySelect = document.getElementById('purchaseCurrency');
        const dataTypeSelect = document.getElementById('purchaseDataType');
        const currentCurrency = currencySelect ? currencySelect.value : 'EUR';
        const currentDataType = dataTypeSelect ? dataTypeSelect.value : 'quantity';

        updateRevenueDisplay(currentCurrency, currentDataType);
        renderPurchaseChart();
        attachEventListeners();
    }

    /**
     * Render the purchase chart
     */
    function renderPurchaseChart() {
        const chartType = document.getElementById('purchaseChartType').value;
        const dataType = document.getElementById('purchaseDataType').value;
        const currency = document.getElementById('purchaseCurrency').value;

        const traces = createTraces(chartType, dataType, currency);
        const layout = createLayout(dataType, currency);
        const config = createConfig();

        Plotly.newPlot('purchaseChart', traces, layout, config);
    }

    /**
     * Create chart traces for each product
     */
    function createTraces(chartType, dataType, currency) {
        const traces = [];
        const colors = [
            '#0d6efd', '#198754', '#dc3545', '#ffc107',
            '#6f42c1', '#fd7e14', '#20c997', '#0dcaf0',
            '#d63384', '#6610f2'
        ];
        let colorIndex = 0;

        // Select the correct product data based on data type and currency
        let products;
        if (dataType === 'total_products' || dataType === 'total_revenue') {
            // Use combined data (both currencies)
            products = purchaseChartData.products_total;
        } else {
            // Use currency-specific data
            products = currency === 'EUR' ? purchaseChartData.products_eur : purchaseChartData.products_usd;
        }

        Object.keys(products).forEach(productName => {
            const productData = products[productName];
            const color = colors[colorIndex % colors.length];

            let yData;
            if (dataType === 'quantity') {
                yData = productData.quantities;
            } else if (dataType === 'total_products') {
                // Use combined quantities
                yData = productData.quantities;
            } else if (dataType === 'amount') {
                yData = productData.amounts;
            } else if (dataType === 'total_revenue') {
                // Use combined total revenue (both currencies converted) based on selected display currency
                yData = currency === 'EUR' ? productData.amounts_eur_total : productData.amounts_usd_total;
            } else {
                yData = productData.quantities;
            }

            const trace = {
                x: productData.dates,
                y: yData,
                name: productName,
                type: getPlotlyChartType(chartType),
                mode: chartType === 'line' ? 'lines+markers' : undefined,
                fill: chartType === 'area' ? 'tonexty' : undefined,
                marker: {
                    color: color,
                    size: chartType === 'line' ? 8 : undefined,
                    line: chartType === 'line' ? {
                        color: 'white',
                        width: 1
                    } : undefined
                },
                line: chartType === 'line' || chartType === 'area' ? {
                    color: color,
                    width: 3,
                    shape: 'spline'
                } : undefined,
                hovertemplate: createHoverTemplate(dataType, productName, currency)
            };

            traces.push(trace);
            colorIndex++;
        });

        return traces;
    }

    /**
     * Get Plotly chart type based on selection
     */
    function getPlotlyChartType(chartType) {
        if (chartType === 'line' || chartType === 'area') {
            return 'scatter';
        }
        return 'bar';
    }

    /**
     * Create hover template
     */
    function createHoverTemplate(dataType, productName, currency) {
        const currencySymbol = currency === 'EUR' ? '€' : '$';

        if (dataType === 'quantity') {
            return '<b>' + productName + '</b><br>' +
                   'Date: %{x|%Y-%m-%d}<br>' +
                   'Quantity: %{y}<br>' +
                   '<extra></extra>';
        } else if (dataType === 'total_products') {
            return '<b>' + productName + '</b><br>' +
                   'Date: %{x|%Y-%m-%d}<br>' +
                   'Total Products Sold: %{y}<br>' +
                   '<extra></extra>';
        } else if (dataType === 'amount') {
            return '<b>' + productName + '</b><br>' +
                   'Date: %{x|%Y-%m-%d}<br>' +
                   'Amount: ' + currencySymbol + '%{y:,.2f}<br>' +
                   '<extra></extra>';
        } else if (dataType === 'total_revenue') {
            return '<b>' + productName + '</b><br>' +
                   'Date: %{x|%Y-%m-%d}<br>' +
                   'Total Revenue: ' + currencySymbol + '%{y:,.2f}<br>' +
                   '<extra></extra>';
        } else {
            return '<b>' + productName + '</b><br>' +
                   'Date: %{x|%Y-%m-%d}<br>' +
                   'Value: %{y}<br>' +
                   '<extra></extra>';
        }
    }

    /**
     * Create chart layout
     */
    function createLayout(dataType, currency) {
        const currencySymbol = currency === 'EUR' ? '€' : '$';

        let chartTitle, yAxisTitle, tickFormat, tickPrefix;

        if (dataType === 'quantity') {
            chartTitle = 'Product Purchases (Quantity)';
            yAxisTitle = 'Quantity Sold';
            tickFormat = ',';
            tickPrefix = '';
        } else if (dataType === 'total_products') {
            chartTitle = 'Total Products Sold';
            yAxisTitle = 'Total Products Sold';
            tickFormat = ',';
            tickPrefix = '';
        } else if (dataType === 'amount') {
            chartTitle = 'Product Purchases (Revenue)';
            yAxisTitle = 'Revenue (' + currencySymbol + ')';
            tickFormat = ',.2f';
            tickPrefix = currencySymbol;
        } else if (dataType === 'total_revenue') {
            chartTitle = 'Total Revenue';
            yAxisTitle = 'Total Revenue (' + currencySymbol + ')';
            tickFormat = ',.2f';
            tickPrefix = currencySymbol;
        } else {
            chartTitle = 'Product Purchases';
            yAxisTitle = 'Value';
            tickFormat = ',';
            tickPrefix = '';
        }

        return {
            title: {
                text: chartTitle,
                font: {
                    size: 18,
                    family: 'Arial, sans-serif',
                    color: '#333'
                }
            },
            xaxis: {
                title: {
                    text: 'Date',
                    font: { size: 14, color: '#666' }
                },
                type: 'date',
                tickformat: '%Y-%m-%d',
                gridcolor: '#e5e5e5',
                showgrid: true,
                zeroline: false
            },
            yaxis: {
                title: {
                    text: yAxisTitle,
                    font: { size: 14, color: '#666' }
                },
                gridcolor: '#e5e5e5',
                showgrid: true,
                zeroline: false,
                tickformat: tickFormat,
                tickprefix: tickPrefix
            },
            hovermode: 'closest',
            showlegend: true,
            legend: {
                x: 1.02,
                xanchor: 'left',
                y: 1,
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: '#ddd',
                borderwidth: 1,
                font: { size: 12 }
            },
            margin: {
                t: 60,
                r: 150,
                b: 80,
                l: 80
            },
            plot_bgcolor: '#fafafa',
            paper_bgcolor: 'white',
            font: {
                family: 'Arial, sans-serif',
                size: 12,
                color: '#333'
            }
        };
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
            scrollZoom: false,
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

    // Expose init function globally if needed
    window.initPurchaseChart = initPurchaseChart;

})();