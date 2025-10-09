(function () {
    const script = document.currentScript;
    if (!script) {
        return;
    }

    const loginUrl = script.dataset.loginUrl;
    if (!loginUrl) {
        return;
    }

    window.location.href = loginUrl;
})();
