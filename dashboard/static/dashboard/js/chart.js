// Dashboard Chart Configuration and Initialization

let currentChart = null; // Store current chart instance
let chartData = {}; // Store chart data globally

/**
 * Initialize chart with different types and data filters
 * @param {Object} data - Object containing all datasets
 * @param {String} chartType - Type of chart ('line', 'bar', 'area', 'mixed')
 * @param {String} dataFilter - Data filter type
 */
function initChart(data, chartType = 'bar', dataFilter = 'all') {
    const ctx = document.getElementById('leadsChart');

    if (!ctx) {
        console.error('Canvas element not found');
        return;
    }

    // Destroy existing chart if it exists
    if (currentChart) {
        currentChart.destroy();
    }

    // Dataset configurations
    const allLeadsDataset = {
        label: 'All Leads',
        data: data.leadCounts,
        borderColor: '#6c757d',
        backgroundColor: chartType === 'bar' ? 'rgba(108, 117, 125, 0.7)' : 'rgba(108, 117, 125, 0.2)',
        borderWidth: 3,
        pointRadius: chartType === 'line' ? 5 : 0,
        pointHoverRadius: 7,
        pointBackgroundColor: '#6c757d',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        fill: chartType === 'area' || chartType === 'line',
        tension: 0.4
    };

    const wonLeadsDataset = {
        label: 'Won Leads',
        data: data.wonLeadCounts,
        borderColor: '#198754',
        backgroundColor: chartType === 'bar' ? 'rgba(25, 135, 84, 0.7)' : 'rgba(25, 135, 84, 0.2)',
        borderWidth: 3,
        pointRadius: chartType === 'line' ? 5 : 0,
        pointHoverRadius: 7,
        pointBackgroundColor: '#198754',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        fill: chartType === 'area' || chartType === 'line',
        tension: 0.4
    };

    const lostLeadsDataset = {
        label: 'Lost Leads',
        data: data.lostLeadCounts,
        borderColor: '#dc3545',
        backgroundColor: chartType === 'bar' ? 'rgba(220, 53, 69, 0.7)' : 'rgba(220, 53, 69, 0.2)',
        borderWidth: 3,
        pointRadius: chartType === 'line' ? 5 : 0,
        pointHoverRadius: 7,
        pointBackgroundColor: '#dc3545',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        fill: chartType === 'area' || chartType === 'line',
        tension: 0.4
    };

    const contactedLeadsDataset = {
        label: 'Contacted Leads',
        data: data.contactedLeadCounts,
        borderColor: '#ffc107',
        backgroundColor: chartType === 'bar' ? 'rgba(255, 193, 7, 0.7)' : 'rgba(255, 193, 7, 0.2)',
        borderWidth: 3,
        pointRadius: chartType === 'line' ? 5 : 0,
        pointHoverRadius: 7,
        pointBackgroundColor: '#ffc107',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        fill: chartType === 'area' || chartType === 'line',
        tension: 0.4
    };

    const clientDataset = {
        label: 'All Clients',
        data: data.clientCounts,
        borderColor: '#0d6efd',
        backgroundColor: chartType === 'bar' ? 'rgba(13, 110, 253, 0.7)' : 'rgba(13, 110, 253, 0.2)',
        borderWidth: 3,
        pointRadius: chartType === 'line' ? 5 : 0,
        pointHoverRadius: 7,
        pointBackgroundColor: '#0d6efd',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        fill: chartType === 'area' || chartType === 'line',
        tension: 0.4
    };

    // Select datasets based on filter
    let datasets = [];
    switch(dataFilter) {
        case 'all':
            datasets = [allLeadsDataset, clientDataset];
            break;
        case 'all_leads':
            datasets = [allLeadsDataset];
            break;
        case 'lead_status':
            datasets = [wonLeadsDataset, lostLeadsDataset, contactedLeadsDataset];
            break;
        case 'won_leads':
            datasets = [wonLeadsDataset];
            break;
        case 'lost_leads':
            datasets = [lostLeadsDataset];
            break;
        case 'contacted_leads':
            datasets = [contactedLeadsDataset];
            break;
        case 'clients':
            datasets = [clientDataset];
            break;
        default:
            datasets = [allLeadsDataset, clientDataset];
    }

    // Configure chart type
    let type = 'line';

    if (chartType === 'bar') {
        type = 'bar';
    } else if (chartType === 'area') {
        type = 'line';
        datasets.forEach(ds => ds.fill = true);
    } else if (chartType === 'mixed' && datasets.length > 1) {
        type = 'bar';
        datasets[0].type = 'line';
        datasets[0].order = 1;
        for (let i = 1; i < datasets.length; i++) {
            datasets[i].type = 'bar';
            datasets[i].order = 2;
        }
    }

    currentChart = new Chart(ctx.getContext('2d'), {
        type: type,
        data: {
            labels: data.dates,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 13
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        title: function(context) {
                            return 'Date: ' + context[0].label;
                        },
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 11
                        },
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        display: chartType === 'bar' ? true : false,
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            },
            interaction: {
                mode: 'index',
                axis: 'x',
                intersect: false
            }
        }
    });

    return currentChart;
}

/**
 * Update chart based on current selections
 */
function updateChart() {
    const chartType = document.getElementById('chartType')?.value || 'bar';
    const dataFilter = document.getElementById('dataFilter')?.value || 'all';

    initChart(chartData, chartType, dataFilter);
}

/**
 * Initialize chart type selector
 */
function initChartTypeSelector() {
    const chartTypeSelect = document.getElementById('chartType');

    if (chartTypeSelect) {
        chartTypeSelect.addEventListener('change', updateChart);
    }
}

/**
 * Initialize data filter selector
 */
function initDataFilterSelector() {
    const dataFilterSelect = document.getElementById('dataFilter');

    if (dataFilterSelect) {
        dataFilterSelect.addEventListener('change', updateChart);
    }
}

/**
 * Initialize period filter auto-submit
 */
function initPeriodFilter() {
    const periodSelect = document.getElementById('period');

    if (periodSelect) {
        periodSelect.addEventListener('change', function() {
            this.form.submit();
        });
    }
}

/**
 * Update date/time display
 */
function updateDateTime() {
    const dateTimeElement = document.getElementById('dashboard-datetime');

    if (!dateTimeElement) {
        return;
    }

    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: '2-digit', day: '2-digit' };
    const datePart = now.toLocaleDateString(undefined, options);
    const timePart = now.toLocaleTimeString(undefined, { hour12: false });
    dateTimeElement.textContent = datePart + ' ' + timePart;
}

/**
 * Initialize dashboard functionality
 * @param {Object} config - Configuration object with all data
 */
function initDashboard(config) {
    // Store data globally
    chartData = {
        dates: config.dates,
        leadCounts: config.leadCounts,
        wonLeadCounts: config.wonLeadCounts,
        lostLeadCounts: config.lostLeadCounts,
        contactedLeadCounts: config.contactedLeadCounts,
        clientCounts: config.clientCounts,
    };

    // Initialize chart if data is provided
    if (config.dates) {
        const initialChartType = document.getElementById('chartType')?.value || 'bar';
        const initialDataFilter = document.getElementById('dataFilter')?.value || 'all';

        initChart(chartData, initialChartType, initialDataFilter);

        initChartTypeSelector();
        initDataFilterSelector();
    }

    // Initialize period filter
    initPeriodFilter();

    // Initialize and update date/time
    updateDateTime();
    setInterval(updateDateTime, 1000);
}

// Export for use in templates
if (typeof window !== 'undefined') {
    window.initDashboard = initDashboard;
}