/**
 * Spolka App – JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {

    // === Podwójne kliknięcie na wiersz tabeli → przejście do szczegółów ===
    document.querySelectorAll('.data-row').forEach(function (row) {
        row.addEventListener('dblclick', function () {
            const url = this.dataset.url;
            if (url) {
                window.location.href = url;
            }
        });
    });

    // === Auto-dismiss alertów po 5 sekundach ===
    document.querySelectorAll('.alert').forEach(function (alert) {
        setTimeout(function () {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(function () { alert.remove(); }, 300);
        }, 5000);
    });

    // === Podświetlenie zaznaczonego wiersza ===
    document.querySelectorAll('.data-row').forEach(function (row) {
        row.addEventListener('click', function () {
            document.querySelectorAll('.data-row').forEach(function (r) {
                r.classList.remove('selected');
            });
            this.classList.add('selected');
        });
    });
});
