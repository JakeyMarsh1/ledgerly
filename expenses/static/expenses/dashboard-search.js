(function () {
    const form = document.querySelector('form[data-search-url]');
    if (!form) {
        return;
    }

    const input = form.querySelector('input[name="q"]');
    if (!input) {
        return;
    }

    const searchUrl = form.dataset.searchUrl || '';
    const resultsSelector = form.dataset.resultsTarget || '';
    const messageSelector = form.dataset.messageTarget || '';
    const resultsContainer = resultsSelector ? document.querySelector(resultsSelector) : null;
    const messageElement = messageSelector ? document.querySelector(messageSelector) : null;
    const defaultTemplate = document.getElementById('search-default-template');
    const defaultHTML = defaultTemplate ? defaultTemplate.innerHTML : '';
    const defaultHasResults = defaultTemplate ? defaultTemplate.dataset.hasResults === 'true' : Boolean(defaultHTML.trim());

    if (!searchUrl || !resultsContainer) {
        return;
    }

    let debounceHandle = null;
    let searchController = null;

    const abortSearch = () => {
        if (searchController) {
            searchController.abort();
            searchController = null;
        }
    };

    const updateMessage = (state, term = '') => {
        if (!messageElement) {
            return;
        }

        const defaultMessage = messageElement.dataset.defaultMessage || '';
        const emptyMessage = messageElement.dataset.emptyMessage || '';
        const foundPrefix = messageElement.dataset.foundPrefix || '';
        const foundSuffix = messageElement.dataset.foundSuffix || '';

        if (state === 'results') {
            messageElement.textContent = `${foundPrefix}${term}${foundSuffix}`;
        } else if (state === 'empty') {
            messageElement.textContent = emptyMessage;
        } else {
            messageElement.textContent = defaultMessage;
        }
    };

    const renderResults = (html) => {
        resultsContainer.innerHTML = html;
        if (html.trim()) {
            resultsContainer.classList.remove('d-none');
        } else {
            resultsContainer.classList.add('d-none');
        }
    };

    const resetToDefault = () => {
        if (defaultHTML.trim()) {
            renderResults(defaultHTML);
        } else {
            renderResults('');
        }
        updateMessage(defaultHasResults ? 'default' : 'empty');
    };

    const fetchSearchResults = async (term) => {
        const url = new URL(searchUrl, window.location.origin);
        url.searchParams.set('q', term);

        abortSearch();
        searchController = new AbortController();

        try {
            const response = await fetch(url.toString(), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                signal: searchController.signal,
            });
            if (!response.ok) {
                throw new Error('Failed to fetch search results');
            }
            const data = await response.json();
            renderResults(data.html || '');
            if (typeof data.count === 'number' && data.count > 0) {
                updateMessage('results', term);
            } else {
                updateMessage('empty');
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                return;
            }
            resetToDefault();
        } finally {
            searchController = null;
        }
    };

    const scheduleSearch = (term) => {
        if (debounceHandle) {
            window.clearTimeout(debounceHandle);
        }
        debounceHandle = window.setTimeout(() => {
            fetchSearchResults(term);
        }, 250);
    };

    input.addEventListener('input', () => {
        const term = input.value.trim();

        if (!term) {
            if (debounceHandle) {
                window.clearTimeout(debounceHandle);
                debounceHandle = null;
            }
            abortSearch();
            resetToDefault();
            return;
        }

        scheduleSearch(term);
    });

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        const term = input.value.trim();

        if (!term) {
            abortSearch();
            resetToDefault();
            return;
        }

        if (debounceHandle) {
            window.clearTimeout(debounceHandle);
            debounceHandle = null;
        }
        fetchSearchResults(term);
    });

    const initialTerm = input.value.trim();
    if (!initialTerm) {
        resetToDefault();
    } else {
        updateMessage('results', initialTerm);
    }

})();
