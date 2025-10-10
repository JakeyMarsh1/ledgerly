(function () {
    if (typeof document === 'undefined') {
        return;
    }

    const modals = document.querySelectorAll('.modal');
    if (!modals.length) {
        return;
    }

    modals.forEach((modal) => {
        let lastExternalFocus = null;

        modal.addEventListener('show.bs.modal', () => {
            const activeElement = document.activeElement;
            if (activeElement && !modal.contains(activeElement)) {
                lastExternalFocus = activeElement;
            } else {
                lastExternalFocus = null;
            }
        });

        modal.addEventListener('hide.bs.modal', () => {
            const activeElement = document.activeElement;
            if (activeElement && modal.contains(activeElement) && typeof activeElement.blur === 'function') {
                activeElement.blur();
            }
        });

        modal.addEventListener('hidden.bs.modal', () => {
            if (lastExternalFocus && typeof lastExternalFocus.focus === 'function') {
                lastExternalFocus.focus({ preventScroll: true });
            }
            lastExternalFocus = null;
        });
    });
})();
