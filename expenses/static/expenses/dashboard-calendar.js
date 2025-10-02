(function () {
    'use strict';

    const modalEl = document.getElementById('transactionCalendarModal');
    if (!modalEl) {
        return;
    }

    const calendarUrl = modalEl.dataset.calendarUrl;
    if (!calendarUrl) {
        return;
    }

    const contentEl = modalEl.querySelector('.js-calendar-content');
    const loadingEl = modalEl.querySelector('.js-calendar-loading');
    const errorEl = modalEl.querySelector('.js-calendar-error');
    const gridEl = modalEl.querySelector('.js-calendar-grid');
    const monthLabelEl = modalEl.querySelector('.js-calendar-month-label');
    const selectedDateEl = modalEl.querySelector('.js-calendar-selected-date');
    const transactionsListEl = modalEl.querySelector('.js-calendar-transaction-list');
    const emptyStateEl = modalEl.querySelector('.js-calendar-empty');
    const addIncomeButton = modalEl.querySelector('.js-calendar-add-income');
    const addExpenseButton = modalEl.querySelector('.js-calendar-add-expense');
    const prevButton = modalEl.querySelector('.js-calendar-nav-prev');
    const nextButton = modalEl.querySelector('.js-calendar-nav-next');

    if (
        !gridEl ||
        !monthLabelEl ||
        !selectedDateEl ||
        !transactionsListEl ||
        !emptyStateEl ||
        !addIncomeButton ||
        !addExpenseButton ||
        !prevButton ||
        !nextButton
    ) {
        return;
    }

    let currentYear;
    let currentMonth;
    let selectedDate = null;
        let calendarData = new Map();
        let dayButtons = new Map();
    let todayIso = '';
    let isLoadingMonth = false;
    let hasLoadedOnce = false;

    const monthFormatter = new Intl.DateTimeFormat(undefined, {
        month: 'long',
        year: 'numeric',
    });
    const dateFormatter = new Intl.DateTimeFormat(undefined, {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
    });

    const pad = (value) => String(value).padStart(2, '0');

    const buildDateKey = (year, month, day) => `${year}-${pad(month)}-${pad(day)}`;

    const setLoading = (loading) => {
        isLoadingMonth = loading;
        if (loadingEl) {
            loadingEl.classList.toggle('d-none', !loading);
        }
        if (contentEl) {
            contentEl.classList.toggle('d-none', loading);
        }
    };

    const showError = (message) => {
        if (!errorEl) {
            return;
        }
        errorEl.textContent = message;
        errorEl.classList.remove('d-none');
    };

    const clearError = () => {
        if (!errorEl) {
            return;
        }
        errorEl.textContent = '';
        errorEl.classList.add('d-none');
    };

    const renderTransactions = (dateKey) => {
        if (!selectedDateEl || !transactionsListEl || !emptyStateEl) {
            return;
        }

        const parts = (dateKey || '').split('-').map(Number);
        if (parts.length === 3 && parts.every((value) => !Number.isNaN(value))) {
            const displayDate = new Date(parts[0], parts[1] - 1, parts[2]);
            selectedDateEl.textContent = dateFormatter.format(displayDate);
        } else {
            selectedDateEl.textContent = dateKey || '—';
        }

        addIncomeButton.disabled = !dateKey;
        addExpenseButton.disabled = !dateKey;

        if (dateKey) {
            addIncomeButton.dataset.selectedDate = dateKey;
            addExpenseButton.dataset.selectedDate = dateKey;
        } else {
            delete addIncomeButton.dataset.selectedDate;
            delete addExpenseButton.dataset.selectedDate;
        }

        transactionsListEl.innerHTML = '';

        const transactions = calendarData.get(dateKey) || [];
        const listContainer = transactionsListEl.parentElement;
        if (listContainer) {
            listContainer.scrollTop = 0;
        }

        if (!transactions.length) {
            transactionsListEl.classList.add('d-none');
            emptyStateEl.classList.remove('d-none');
            return;
        }

        emptyStateEl.classList.add('d-none');
        transactionsListEl.classList.remove('d-none');

        transactions.forEach((transaction) => {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item bg-transparent px-0 py-2';

            const row = document.createElement('div');
            row.className = 'd-flex justify-content-between align-items-start gap-3 flex-wrap';

            const info = document.createElement('div');
            info.className = 'flex-grow-1';

            const title = document.createElement('h3');
            title.className = 'h6 mb-1 text-primary text-truncate';
            title.textContent = transaction.name || 'Transaction';
            info.appendChild(title);

            const meta = document.createElement('div');
            meta.className = 'text-secondary small text-break';
            const fragments = [];
            if (transaction.type_display) {
                fragments.push(transaction.type_display);
            }
            if (transaction.category) {
                fragments.push(transaction.category);
            }
            meta.textContent = fragments.length ? fragments.join(' · ') : '—';
            info.appendChild(meta);

            if (transaction.note) {
                const note = document.createElement('div');
                note.className = 'text-secondary small fst-italic mt-1';
                note.textContent = transaction.note;
                info.appendChild(note);
            }

            const actions = document.createElement('div');
            actions.className = 'text-end d-flex flex-column align-items-end gap-1';

            const amount = document.createElement('span');
            amount.className = `fw-semibold ${transaction.type === 'OUTGO' ? 'text-danger' : 'text-success'}`;
            amount.textContent = transaction.amount_display || '';
            actions.appendChild(amount);

            const viewButton = document.createElement('button');
            viewButton.type = 'button';
            viewButton.className = 'btn btn-link btn-sm p-0 text-decoration-none text-primary js-view-transaction';
            viewButton.textContent = 'View / Edit';
            if (transaction.detail_url) {
                viewButton.dataset.transactionUrl = transaction.detail_url;
            }
            actions.appendChild(viewButton);

            row.append(info, actions);
            listItem.appendChild(row);
            transactionsListEl.appendChild(listItem);
        });
    };

    const selectDate = (dateKey) => {
        if (!dateKey || !dayButtons.has(dateKey)) {
            const iterator = dayButtons.keys().next();
            if (iterator.done) {
                selectedDate = null;
                renderTransactions(null);
                return;
            }
            selectDate(iterator.value);
            return;
        }

        selectedDate = dateKey;
        dayButtons.forEach((button, key) => {
            const isSelected = key === dateKey;
            button.classList.toggle('is-selected', isSelected);
            button.setAttribute('aria-pressed', isSelected ? 'true' : 'false');
        });

        renderTransactions(dateKey);
    };

    const renderCalendar = () => {
        dayButtons = new Map();
        gridEl.innerHTML = '';

        const firstOfMonth = new Date(currentYear, currentMonth - 1, 1);
        const leadingSpacers = firstOfMonth.getDay();
        for (let i = 0; i < leadingSpacers; i += 1) {
            const spacer = document.createElement('div');
            spacer.className = 'calendar-day calendar-day--empty';
            spacer.setAttribute('aria-hidden', 'true');
            gridEl.appendChild(spacer);
        }

        const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
        for (let day = 1; day <= daysInMonth; day += 1) {
            const dateKey = buildDateKey(currentYear, currentMonth, day);
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'calendar-day';
            button.dataset.date = dateKey;
            button.setAttribute('aria-pressed', 'false');

            const displayDate = new Date(currentYear, currentMonth - 1, day);
            button.setAttribute('aria-label', dateFormatter.format(displayDate));

            const count = calendarData.has(dateKey) ? calendarData.get(dateKey).length : 0;
            if (count > 0) {
                button.classList.add('has-transactions');
            }
            if (todayIso === dateKey) {
                button.classList.add('is-today');
            }

            const numberEl = document.createElement('span');
            numberEl.className = 'calendar-day__number';
            numberEl.textContent = String(day);
            button.appendChild(numberEl);

            if (count > 0) {
                const badge = document.createElement('span');
                badge.className = 'calendar-day__badge';
                badge.textContent = String(count);
                badge.setAttribute('aria-hidden', 'true');
                button.appendChild(badge);
            }

            button.addEventListener('click', () => {
                if (isLoadingMonth) {
                    return;
                }
                selectDate(dateKey);
            });

            dayButtons.set(dateKey, button);
            gridEl.appendChild(button);
        }

        const totalCells = leadingSpacers + daysInMonth;
        const trailingSpacers = (7 - (totalCells % 7)) % 7;
        for (let i = 0; i < trailingSpacers; i += 1) {
            const spacer = document.createElement('div');
            spacer.className = 'calendar-day calendar-day--empty';
            spacer.setAttribute('aria-hidden', 'true');
            gridEl.appendChild(spacer);
        }
    };

    const populateCalendar = (data) => {
        currentYear = Number(data.year);
        currentMonth = Number(data.month);
        todayIso = data.today || todayIso;

        const days = Array.isArray(data.days) ? data.days : [];
        calendarData = new Map(days.map((day) => [day.date, Array.isArray(day.transactions) ? day.transactions : []]));

        if (monthLabelEl) {
            const labelDate = new Date(currentYear, currentMonth - 1, 1);
            monthLabelEl.textContent = data.month_label || monthFormatter.format(labelDate);
        }

        renderCalendar();

        let initialDate = data.initial_date;
        const monthPrefix = `${currentYear}-${pad(currentMonth)}`;
        if (!initialDate || !initialDate.startsWith(monthPrefix)) {
            if (todayIso && todayIso.startsWith(monthPrefix)) {
                initialDate = todayIso;
            } else if (calendarData.size > 0) {
                initialDate = calendarData.keys().next().value;
            } else {
                initialDate = buildDateKey(currentYear, currentMonth, 1);
            }
        }

        selectDate(initialDate);
    };

    const fetchMonth = async (year, month) => {
        const url = new URL(calendarUrl, window.location.origin);
        url.searchParams.set('year', year);
        url.searchParams.set('month', month);

        const response = await fetch(url.toString(), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        });

        if (!response.ok) {
            throw new Error('Failed to fetch calendar data.');
        }

        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            throw new Error('Unexpected response format.');
        }

        return response.json();
    };

    const loadMonth = async (year, month) => {
        setLoading(true);
        clearError();
        try {
            const data = await fetchMonth(year, month);
            populateCalendar(data);
        } catch (error) {
            showError('Unable to load calendar data right now. Please try again shortly.');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    prevButton.addEventListener('click', () => {
        if (isLoadingMonth || typeof currentYear === 'undefined') {
            return;
        }
        const previous = new Date(currentYear, currentMonth - 2, 1);
        loadMonth(previous.getFullYear(), previous.getMonth() + 1);
    });

    nextButton.addEventListener('click', () => {
        if (isLoadingMonth || typeof currentYear === 'undefined') {
            return;
        }
        const next = new Date(currentYear, currentMonth, 1);
        loadMonth(next.getFullYear(), next.getMonth() + 1);
    });

    const openTransactionModal = (type) => {
        if (!selectedDate || typeof bootstrap === 'undefined') {
            return;
        }

        const targetId = type === 'INCOME' ? 'addIncomeModal' : 'addExpenseModal';
        const targetEl = document.getElementById(targetId);
        if (!targetEl) {
            return;
        }

        const dateField = targetEl.querySelector('input[name="occurred_on"]');
        if (dateField) {
            dateField.value = selectedDate;
        }

        const calendarInstance = bootstrap.Modal.getInstance(modalEl);
        if (calendarInstance) {
            calendarInstance.hide();
        }

        const targetInstance = bootstrap.Modal.getOrCreateInstance(targetEl);
        targetInstance.show();
    };

    addIncomeButton.addEventListener('click', () => openTransactionModal('INCOME'));
    addExpenseButton.addEventListener('click', () => openTransactionModal('OUTGO'));

    modalEl.addEventListener('show.bs.modal', () => {
        clearError();
        if (loadingEl) {
            loadingEl.classList.remove('d-none');
        }
        if (contentEl) {
            contentEl.classList.add('d-none');
        }
    });

    modalEl.addEventListener('shown.bs.modal', () => {
        if (hasLoadedOnce) {
            return;
        }
        hasLoadedOnce = true;
        const today = new Date();
        loadMonth(today.getFullYear(), today.getMonth() + 1);
    });
})();
