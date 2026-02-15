/**
 * Fix Bootstrap 4 tabs in jazzmin admin.
 * jQuery loads twice (Django admin head + jazzmin body), which can cause
 * Bootstrap's data-api event delegation to not bind correctly.
 * This script re-binds tab click handlers as a safety net.
 */
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var tabLinks = document.querySelectorAll('[data-toggle="pill"], [data-toggle="tab"]');
        if (!tabLinks.length) return;

        tabLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                var targetId = this.getAttribute('href');
                if (!targetId || targetId === '#') return;

                var tabContent = document.querySelector('.tab-content');
                if (!tabContent) return;

                // Deactivate all tabs and panes
                var allLinks = this.closest('ul').querySelectorAll('.nav-link');
                allLinks.forEach(function(l) { l.classList.remove('active'); });

                var allPanes = tabContent.querySelectorAll('.tab-pane');
                allPanes.forEach(function(p) {
                    p.classList.remove('active', 'show');
                });

                // Activate clicked tab and its pane
                this.classList.add('active');
                var pane = document.querySelector(targetId);
                if (pane) {
                    pane.classList.add('active', 'show');
                }

                // Update URL hash
                if (history.pushState) {
                    history.pushState(null, null, targetId);
                }
            });
        });
    });
})();
