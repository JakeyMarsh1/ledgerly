(function () {
    const monthsEl = document.getElementById('chart-months');
    const incomeEl = document.getElementById('chart-income');
    const expenseEl = document.getElementById('chart-expense');
    if (!monthsEl || !incomeEl || !expenseEl) {
        return;
    }

    const labels = JSON.parse(monthsEl.textContent);
    const incomeData = JSON.parse(incomeEl.textContent);
    const expenseData = JSON.parse(expenseEl.textContent);

    const ctx = document.getElementById('monthlyChart');
    if (!ctx || typeof Chart === 'undefined') {
        return;
    }

    new Chart(ctx, {
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
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    borderColor: 'rgba(239, 68, 68, 1)',
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    tension: 0.3,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => `${value}¢`,
                    },
                },
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#fff',
                    },
                },
            },
        },
    });
})();
