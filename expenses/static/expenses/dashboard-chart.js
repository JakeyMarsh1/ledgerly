(function () {
    const monthsEl = document.getElementById('chart-months');
    const incomeEl = document.getElementById('chart-income');
    const expenseEl = document.getElementById('chart-expense');
    if (!monthsEl || !incomeEl || !expenseEl) {
        return;
    }

    const labels = JSON.parse(monthsEl.textContent);
    const incomeRaw = JSON.parse(incomeEl.textContent).map((value) => Number(value));
    const expenseRaw = JSON.parse(expenseEl.textContent).map((value) => Number(value));

    if (incomeRaw.some((value) => Number.isNaN(value)) || expenseRaw.some((value) => Number.isNaN(value))) {
        console.warn('Ledgerly chart skipped: series contains non-numeric values.', {
            incomeRaw,
            expenseRaw,
        });
        return;
    }

    if (labels.length !== incomeRaw.length || labels.length !== expenseRaw.length) {
        console.warn('Ledgerly chart mismatch: label count does not equal series length.', {
            labels,
            incomeRaw,
            expenseRaw,
        });
    }

    const ctx = document.getElementById('monthlyChart');
    if (!ctx || typeof Chart === 'undefined') {
        return;
    }

    const currencyCode = ctx.dataset.currencyCode || 'USD';
    const currencySymbol = ctx.dataset.currencySymbol || '$';
    let currencyFormatter;
    try {
        currencyFormatter = new Intl.NumberFormat(undefined, {
            style: 'currency',
            currency: currencyCode,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    } catch (error) {
        console.warn('Ledgerly chart: falling back to symbol formatting.', { error });
        currencyFormatter = {
            format(value) {
                return `${currencySymbol}${value.toFixed(2)}`;
            },
        };
    }

    const incomeData = incomeRaw.map((value) => value / 100);
    const expenseData = expenseRaw.map((value) => value / 100);

    const commonLength = Math.min(labels.length, incomeData.length, expenseData.length);
    if (commonLength < labels.length) {
        labels.length = commonLength;
    }
    incomeData.length = commonLength;
    expenseData.length = commonLength;

    const getDateLabel = (index) => {
        return labels[index] ?? '';
    };

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    borderColor: 'rgba(59, 130, 246, 1)',
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    pointBorderWidth: 0,
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                    pointHitRadius: 10,
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    borderColor: 'rgba(239, 68, 68, 1)',
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    pointBorderWidth: 0,
                    pointBackgroundColor: 'rgba(239, 68, 68, 1)',
                    pointHitRadius: 10,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 12,
                    bottom: 20,
                    left: 16,
                    right: 16,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grace: '10%',
                    ticks: {
                        padding: 8,
                        callback: (value) => currencyFormatter.format(value),
                    },
                },
                x: {
                    ticks: {
                        padding: 8,
                        callback: (value, index) => getDateLabel(index),
                        maxRotation: 0,
                        autoSkip: true,
                        autoSkipPadding: 16,
                    },
                    grid: {
                        display: false,
                    },
                },
            },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    callbacks: {
                        title(items) {
                            if (!items.length) {
                                return '';
                            }
                            return getDateLabel(items[0].dataIndex ?? 0);
                        },
                        label(context) {
                            const value = context.parsed.y ?? 0;
                            const formatted = currencyFormatter.format(value);
                            if (context.dataset && context.dataset.label) {
                                return `${context.dataset.label}: ${formatted}`;
                            }
                            return formatted;
                        },
                    },
                },
            },
        },
    });
    const legendContainer = document.getElementById('monthlyChartLegend');
    if (legendContainer) {
        const renderLegend = () => {
            legendContainer.innerHTML = '';
            chart.data.datasets.forEach((dataset, datasetIndex) => {
                const isVisible = chart.isDatasetVisible(datasetIndex);
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'chart-legend__item';
                if (!isVisible) {
                    item.classList.add('chart-legend__item--muted');
                }
                item.style.color = dataset.borderColor ?? '#fff';
                const orb = document.createElement('span');
                orb.className = 'chart-legend__orb';
                orb.style.backgroundColor = dataset.borderColor ?? '#fff';
                orb.style.boxShadow = `0 0 6px ${dataset.borderColor}, 0 0 12px ${dataset.borderColor}`;
                const label = document.createElement('span');
                label.className = 'chart-legend__label';
                label.textContent = dataset.label;
                item.append(orb, label);
                item.addEventListener('click', () => {
                    const currentlyVisible = chart.isDatasetVisible(datasetIndex);
                    chart.setDatasetVisibility(datasetIndex, !currentlyVisible);
                    chart.update();
                    renderLegend();
                });
                legendContainer.appendChild(item);
            });
        };
        renderLegend();
    }
})();
