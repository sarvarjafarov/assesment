document.addEventListener('DOMContentLoaded', () => {
    const accordion = document.querySelector('#featureAccordion');
    if (accordion) {
        const buttons = accordion.querySelectorAll('[data-feature-button]');
        const accent = accordion.querySelector('.accent-bar');
        const updateAccent = (btn) => {
            const rect = btn.getBoundingClientRect();
            const parentRect = accordion.getBoundingClientRect();
            if (accent) {
                const offset = rect.top - parentRect.top - 4;
                accent.style.transform = `translateY(${offset}px)`;
                accent.style.height = `${rect.height - 8}px`;
            }
        };
        buttons.forEach((btn) => {
            btn.addEventListener('click', () => {
                buttons.forEach((b) => b.classList.remove('is-active'));
                btn.classList.add('is-active');
                updateAccent(btn);
            });
        });
        const active = accordion.querySelector('.accordion-item.is-active');
        if (active) {
            updateAccent(active);
        }
        window.addEventListener('resize', () => {
            const current = accordion.querySelector('.accordion-item.is-active');
            if (current) {
                updateAccent(current);
            }
        });
    }
});
