document.addEventListener('DOMContentLoaded', () => {
    const accordion = document.querySelector('#featureAccordion');
    const panelsContainer = document.querySelector('.feature-panels');
    const panels = panelsContainer
        ? panelsContainer.querySelectorAll('[data-feature-panel]')
        : [];
    const setActivePanel = (slug) => {
        if (!panels.length) {
            return;
        }
        panels.forEach((panel) => {
            if (panel.dataset.featurePanel === slug) {
                panel.classList.add('is-active');
            } else {
                panel.classList.remove('is-active');
            }
        });
    };
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
                setActivePanel(btn.dataset.feature);
            });
        });
        const active = accordion.querySelector('.accordion-item.is-active');
        if (active) {
            updateAccent(active);
            setActivePanel(active.dataset.feature);
        }
        window.addEventListener('resize', () => {
            const current = accordion.querySelector('.accordion-item.is-active');
            if (current) {
                updateAccent(current);
            }
        });
    }

    const journeyStages = document.querySelectorAll('.journey-stage');
    if (journeyStages.length) {
        let stageIndex = 0;
        const rotateStages = () => {
            journeyStages.forEach((stage, idx) => {
                stage.classList.toggle('is-active', idx === stageIndex);
            });
            stageIndex = (stageIndex + 1) % journeyStages.length;
        };
        rotateStages();
        setInterval(rotateStages, 4000);
    }

    const testimonialButtons = document.querySelectorAll('[data-testimonial-button]');
    const testimonialPanels = document.querySelectorAll('[data-testimonial-panel]');
    if (testimonialButtons.length && testimonialPanels.length) {
        let activeIndex = 0;
        const setTestimonial = (index) => {
            activeIndex = index;
            testimonialButtons.forEach((btn, idx) => {
                btn.classList.toggle('is-active', idx === index);
            });
            testimonialPanels.forEach((panel, idx) => {
                panel.classList.toggle('is-active', idx === index);
            });
        };
        testimonialButtons.forEach((button) => {
            button.addEventListener('click', () =>
                setTestimonial(Number(button.dataset.testimonialButton))
            );
        });
        setInterval(() => {
            const next = (activeIndex + 1) % testimonialButtons.length;
            setTestimonial(next);
        }, 6000);
    }

    const generateToken = () =>
        `sk_live_${Math.random().toString(36).slice(2, 8)}${Math.random()
            .toString(36)
            .slice(2, 10)}`;

    const tokenButtons = document.querySelectorAll(".token-generate");
    tokenButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const targetSelector = button.dataset.tokenTarget;
            const target = document.querySelector(targetSelector);
            if (!target) {
                return;
            }
            const token = generateToken();
            target.textContent = `X-API-Key: ${token}`;
            button.textContent = "New token generated";
            setTimeout(() => (button.textContent = "Generate mock token"), 2000);
        });
    });

    const copyButtons = document.querySelectorAll(".copy-trigger");
    copyButtons.forEach((btn) => {
        const defaultLabel = btn.dataset.copyLabel || btn.textContent.trim();
        const successLabel = btn.dataset.copySuccess || "Copied!";
        const fallbackLabel = btn.dataset.copyFallback || "Press ⌘C / Ctrl+C";
        btn.dataset.copyLabel = defaultLabel;
        btn.dataset.copySuccess = successLabel;
        btn.dataset.copyFallback = fallbackLabel;
        btn.addEventListener("click", async () => {
            const target = document.querySelector(btn.dataset.copyTarget);
            if (!target) {
                return;
            }
            try {
                await navigator.clipboard.writeText(target.textContent.trim());
                btn.textContent = successLabel;
                setTimeout(() => (btn.textContent = defaultLabel), 1500);
            } catch (err) {
                btn.textContent = fallbackLabel;
                setTimeout(() => (btn.textContent = defaultLabel), 2000);
            }
        });
    });

    const languageSwitchers = document.querySelectorAll("[data-language-switcher]");
    languageSwitchers.forEach((switcher) => {
        const tabs = switcher.querySelectorAll("[data-language-tab]");
        const panels = switcher.querySelectorAll("[data-language-panel]");
        if (!tabs.length || !panels.length) {
            return;
        }
        tabs.forEach((tab) => {
            tab.addEventListener("click", () => {
                const targetKey = tab.dataset.languageTab;
                tabs.forEach((btn) => btn.classList.toggle("is-active", btn === tab));
                panels.forEach((panel) => {
                    panel.classList.toggle(
                        "is-active",
                        panel.dataset.languagePanel === targetKey
                    );
                });
            });
        });
    });

    const longFormInputs = document.querySelectorAll(".long-form-input");
    longFormInputs.forEach((input) => {
        const card = input.closest(".question-card");
        if (!card) {
            return;
        }
        const container = card.querySelector(".answer-preview");
        if (!container) {
            return;
        }
        const charCount = container.querySelector("[data-char-count]");
        const previewBody = container.querySelector("[data-preview-body]");
        if (!previewBody) {
            return;
        }
        const placeholder = previewBody.dataset.placeholder || "Start typing…";
        const minLength =
            Number(input.dataset.minLength || charCount?.dataset.minLength || 0) || 0;
        const updatePreview = () => {
            const value = input.value;
            if (charCount) {
                const label =
                    minLength > 0
                        ? `${value.length} characters · aim for ${minLength}+`
                        : `${value.length} characters`;
                charCount.textContent = label;
                charCount.classList.toggle("is-warning", minLength > 0 && value.length < minLength);
            }
            if (!value.trim()) {
                previewBody.textContent = placeholder;
                previewBody.classList.add("is-empty");
                return;
            }
            previewBody.textContent = value;
            previewBody.classList.remove("is-empty");
        };
        input.addEventListener("input", updatePreview);
        updatePreview();
    });

    const body = document.body;
    const contrastToggle = document.getElementById("contrastToggle");
    const applyContrastPreference = (enabled) => {
        body.classList.toggle("contrast-mode", enabled);
        if (contrastToggle) {
            contrastToggle.setAttribute("aria-pressed", enabled ? "true" : "false");
            contrastToggle.textContent = enabled ? "Standard contrast" : "High contrast";
        }
    };
    const storedPreference = localStorage.getItem("contrast-mode");
    if (storedPreference) {
        applyContrastPreference(storedPreference === "true");
    } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        applyContrastPreference(true);
    }
    if (contrastToggle) {
        contrastToggle.addEventListener("click", () => {
            const enabled = !body.classList.contains("contrast-mode");
            applyContrastPreference(enabled);
            localStorage.setItem("contrast-mode", enabled ? "true" : "false");
        });
    }

    const telemetryState = {
        pasteCount: 0,
        fieldPastes: {},
    };

    document.addEventListener("paste", (event) => {
        const target = event.target;
        if (
            target &&
            (target.matches(".long-form-input") ||
                target.matches("textarea") ||
                target.matches("input[type='text']"))
        ) {
            telemetryState.pasteCount += 1;
            const key = target.name || target.id || "field";
            telemetryState.fieldPastes[key] = (telemetryState.fieldPastes[key] || 0) + 1;
        }
    });

    const captureTelemetryPayload = (form) => {
        const field = form.querySelector("[data-telemetry-field]");
        if (!field) {
            return;
        }
        const payload = {
            pasteCount: telemetryState.pasteCount,
            fieldPastes: telemetryState.fieldPastes,
            deviceHints: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                screen: `${window.screen.width}x${window.screen.height}`,
                viewport: `${window.innerWidth}x${window.innerHeight}`,
            },
            page: window.location.pathname,
        };
        field.value = JSON.stringify(payload);
    };

    document.querySelectorAll("form.question-form").forEach((form) => {
        form.addEventListener("submit", () => captureTelemetryPayload(form));
    });

    const velocityCanvas = document.getElementById("velocityChart");
    if (velocityCanvas && velocityCanvas.getContext) {
        const ctx = velocityCanvas.getContext("2d");
        const points = [52, 48, 44, 40, 36, 33];
        const width = velocityCanvas.width;
        const height = velocityCanvas.height;
        ctx.clearRect(0, 0, width, height);
        ctx.strokeStyle = "#ff8a00";
        ctx.lineWidth = 3;
        ctx.beginPath();
        points.forEach((value, idx) => {
            const x = (idx / (points.length - 1 || 1)) * width;
            const y = height - (value / 60) * height;
            if (idx === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
        ctx.fillStyle = "rgba(255,138,0,0.15)";
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.closePath();
        ctx.fill();
    }
});
