
document.addEventListener("DOMContentLoaded", () => {
    const backButton = document.getElementById("goBackButton");

    if (!backButton) return;

    backButton.addEventListener("click", () => {
        const homeUrl = backButton.dataset.homeUrl;

        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = homeUrl;
        }
    });
});
