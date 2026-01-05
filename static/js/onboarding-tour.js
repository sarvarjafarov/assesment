/**
 * Evalon Onboarding Tour System
 * Lightweight vanilla JS tour with spotlight highlighting
 */

class OnboardingTour {
    constructor(steps, options = {}) {
        this.steps = steps;
        this.currentStep = 0;
        this.options = {
            showProgress: true,
            allowSkip: true,
            showChecklist: true,
            exitOnClickOutside: false,
            ...options
        };

        // DOM elements (created on init)
        this.overlay = null;
        this.spotlight = null;
        this.tooltip = null;
        this.progressBar = null;

        this.init();
    }

    init() {
        // Create overlay structure
        this.createOverlay();
        this.createSpotlight();
        this.createTooltip();
        this.createProgressIndicator();

        // Bind keyboard events
        this.bindKeyboardShortcuts();

        // Start tour
        this.showStep(0);
    }

    createOverlay() {
        this.overlay = document.createElement('div');
        this.overlay.className = 'onboarding-overlay';
        this.overlay.style.cssText = `
            position: fixed;
            inset: 0;
            background: rgba(6, 11, 25, 0.85);
            z-index: 1002;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(this.overlay);

        // Fade in
        requestAnimationFrame(() => {
            this.overlay.style.opacity = '1';
        });
    }

    createSpotlight() {
        this.spotlight = document.createElement('div');
        this.spotlight.className = 'onboarding-spotlight';
        this.spotlight.style.cssText = `
            position: fixed;
            border: 3px solid var(--orange);
            border-radius: 12px;
            box-shadow: 0 0 0 9999px rgba(6, 11, 25, 0.85),
                        0 0 20px rgba(255, 138, 0, 0.5);
            pointer-events: none;
            z-index: 1003;
            transition: all 0.3s ease;
        `;
        document.body.appendChild(this.spotlight);
    }

    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'onboarding-tooltip';
        this.tooltip.innerHTML = `
            <div class="tooltip-content">
                <div class="tooltip-header">
                    <h3 class="tooltip-title"></h3>
                    <button class="tooltip-close" aria-label="Close tour">×</button>
                </div>
                <p class="tooltip-message"></p>
                <div class="tooltip-footer">
                    <div class="tooltip-progress"></div>
                    <div class="tooltip-actions">
                        <button class="btn-previous">Previous</button>
                        <button class="btn-next">Next</button>
                    </div>
                </div>
            </div>
        `;
        this.tooltip.style.cssText = `
            position: fixed;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 12px 32px rgba(6, 11, 25, 0.2);
            padding: 1.5rem;
            max-width: 400px;
            z-index: 1004;
            transition: all 0.3s ease;
        `;
        document.body.appendChild(this.tooltip);

        // Bind button events
        this.tooltip.querySelector('.tooltip-close').onclick = () => this.skipTour();
        this.tooltip.querySelector('.btn-previous').onclick = () => this.previousStep();
        this.tooltip.querySelector('.btn-next').onclick = () => this.nextStep();
    }

    createProgressIndicator() {
        const progressContainer = this.tooltip.querySelector('.tooltip-progress');
        if (this.options.showProgress) {
            progressContainer.innerHTML = `
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <span class="progress-text">Step <span class="step-current">1</span> of <span class="step-total">${this.steps.length}</span></span>
            `;
        }
    }

    showStep(index) {
        if (index < 0 || index >= this.steps.length) return;

        this.currentStep = index;
        const step = this.steps[index];

        // Update tooltip content
        this.tooltip.querySelector('.tooltip-title').textContent = step.title;
        this.tooltip.querySelector('.tooltip-message').textContent = step.message;

        // Update progress
        if (this.options.showProgress) {
            const progress = ((index + 1) / this.steps.length) * 100;
            this.tooltip.querySelector('.progress-fill').style.width = `${progress}%`;
            this.tooltip.querySelector('.step-current').textContent = index + 1;
        }

        // Update button states
        this.tooltip.querySelector('.btn-previous').disabled = index === 0;
        const nextBtn = this.tooltip.querySelector('.btn-next');
        if (index === this.steps.length - 1) {
            nextBtn.textContent = 'Finish';
        } else {
            nextBtn.textContent = 'Next';
        }

        // Position spotlight and tooltip
        this.highlightElement(step.target);

        // Optional: Auto-scroll to element
        if (step.scrollTo !== false) {
            this.scrollToElement(step.target);
        }

        // Optional: Execute custom step action
        if (typeof step.onShow === 'function') {
            step.onShow(this);
        }
    }

    highlightElement(selector) {
        const element = document.querySelector(selector);
        if (!element) {
            console.warn(`Onboarding: Target element not found: ${selector}`);
            return;
        }

        const rect = element.getBoundingClientRect();

        // Position spotlight
        this.spotlight.style.top = `${rect.top - 8}px`;
        this.spotlight.style.left = `${rect.left - 8}px`;
        this.spotlight.style.width = `${rect.width + 16}px`;
        this.spotlight.style.height = `${rect.height + 16}px`;

        // Position tooltip (smart positioning)
        this.positionTooltip(rect);
    }

    positionTooltip(targetRect) {
        const tooltipRect = this.tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const padding = 20;

        let top, left;

        // Try positioning to the right
        if (targetRect.right + tooltipRect.width + padding < viewportWidth) {
            left = targetRect.right + padding;
            top = targetRect.top;
        }
        // Try positioning to the left
        else if (targetRect.left - tooltipRect.width - padding > 0) {
            left = targetRect.left - tooltipRect.width - padding;
            top = targetRect.top;
        }
        // Position below
        else if (targetRect.bottom + tooltipRect.height + padding < viewportHeight) {
            left = Math.max(padding, Math.min(
                targetRect.left,
                viewportWidth - tooltipRect.width - padding
            ));
            top = targetRect.bottom + padding;
        }
        // Position above
        else {
            left = Math.max(padding, Math.min(
                targetRect.left,
                viewportWidth - tooltipRect.width - padding
            ));
            top = targetRect.top - tooltipRect.height - padding;
        }

        this.tooltip.style.top = `${top}px`;
        this.tooltip.style.left = `${left}px`;
    }

    scrollToElement(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'center'
            });
        }
    }

    nextStep() {
        if (this.currentStep < this.steps.length - 1) {
            this.showStep(this.currentStep + 1);
        } else {
            this.completeTour();
        }
    }

    previousStep() {
        if (this.currentStep > 0) {
            this.showStep(this.currentStep - 1);
        }
    }

    skipTour() {
        if (confirm('Are you sure you want to exit the tour? You can restart it anytime from Settings.')) {
            this.destroy();
        }
    }

    completeTour() {
        // Show completion modal/message
        this.showCompletionModal();

        // Mark as complete on backend
        this.markComplete();

        // Destroy tour
        setTimeout(() => this.destroy(), 2000);
    }

    showCompletionModal() {
        const modal = document.createElement('div');
        modal.className = 'onboarding-completion-modal fade-in';
        modal.innerHTML = `
            <div class="completion-card">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--orange);">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                <h2>Tour Complete!</h2>
                <p>You're all set to start hiring. Remember, you can:</p>
                <ul>
                    <li>Send assessment invites</li>
                    <li>Organize candidates with projects</li>
                    <li>Review results and make decisions</li>
                    <li>Track analytics and insights</li>
                </ul>
                <button class="btn btn-primary" onclick="this.parentElement.parentElement.remove()">Get Started</button>
            </div>
        `;
        document.body.appendChild(modal);
    }

    markComplete() {
        // AJAX call to backend
        fetch('/clients/onboarding/complete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: 'action=complete_tour'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Onboarding completed:', data);
        })
        .catch(error => {
            console.error('Error completing onboarding:', error);
        });
    }

    bindKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (!this.overlay) return;

            switch(e.key) {
                case 'ArrowRight':
                case 'Enter':
                    e.preventDefault();
                    this.nextStep();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousStep();
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.skipTour();
                    break;
            }
        });
    }

    destroy() {
        // Fade out and remove
        this.overlay.style.opacity = '0';
        setTimeout(() => {
            this.overlay?.remove();
            this.spotlight?.remove();
            this.tooltip?.remove();
        }, 300);
    }

    getCookie(name) {
        // Django CSRF token helper
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OnboardingTour;
}
