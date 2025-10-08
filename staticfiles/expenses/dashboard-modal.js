(function () {
    const modalElement = document.getElementById('transactionModal');
    if (!modalElement) {
        return;
    }

    const modal = new bootstrap.Modal(modalElement, {
        backdrop: 'static',
    });
    const modalContent = modalElement.querySelector('.modal-content');

    const renderError = (message) => {
        modalContent.innerHTML = `
            <div class="modal-header">
                <h1 class="h5 mb-0">Transaction</h1>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <p class="text-danger mb-0">${message}</p>
            </div>
        `;
    };

    const wireForm = () => {
        const form = modalElement.querySelector('form');
        if (!form) {
            return;
        }

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const submitButton = form.querySelector('[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
            }

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: new FormData(form),
                });

                const contentType = response.headers.get('content-type') || '';
                if (contentType.includes('application/json')) {
                    const data = await response.json();
                    if (data.success) {
                        modal.hide();
                        window.location.reload();
                        return;
                    }
                }

                const html = await response.text();
                modalContent.innerHTML = html;
                wireForm();
            } catch (error) {
                renderError('An unexpected error occurred while saving. Please try again.');
            } finally {
                if (submitButton) {
                    submitButton.disabled = false;
                }
            }
        }, { once: true });
    };

    const loadTransaction = async (url) => {
        modalContent.innerHTML = `
            <div class="modal-body text-center py-5">
                <div class="spinner-border text-primary" role="status" aria-hidden="true"></div>
                <p class="mt-3 mb-0">Loading transaction…</p>
            </div>
        `;

        try {
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to load transaction.');
            }

            const html = await response.text();
            modalContent.innerHTML = html;
            wireForm();
        } catch (error) {
            renderError('Unable to load the selected transaction.');
        }
    };

    document.addEventListener('click', (event) => {
        const trigger = event.target.closest('.js-view-transaction');
        if (!trigger) {
            return;
        }

        const url = trigger.dataset.transactionUrl;
        if (!url) {
            return;
        }

        event.preventDefault();
        modal.show();
        loadTransaction(url);
    });
})();
