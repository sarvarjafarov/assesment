document.addEventListener('DOMContentLoaded', () => {
    const trackEvent = (name, params = {}) => {
        if (typeof window.gtag === 'function' && name) {
            window.gtag('event', name, params);
        }
    };
    window.evalonTrackEvent = trackEvent;

    const parseJson = (value) => {
        if (!value) {
            return {};
        }
        try {
            return JSON.parse(value);
        } catch (error) {
            console.warn('Invalid data-gtag-params value', error);
            return {};
        }
    };

    const buildPayload = (target, defaults = {}) => {
        const payload = { ...defaults };
        if (!target || !target.dataset) {
            return payload;
        }
        const { dataset } = target;
        if (dataset.gtagCategory) {
            payload.event_category = dataset.gtagCategory;
        }
        if (dataset.gtagLabel) {
            payload.event_label = dataset.gtagLabel;
        }
        if (dataset.gtagValue && !Number.isNaN(Number(dataset.gtagValue))) {
            payload.value = Number(dataset.gtagValue);
        }
        if (dataset.gtagCurrency) {
            payload.currency = dataset.gtagCurrency;
        }
        if (dataset.gtagItemName) {
            const item = { item_name: dataset.gtagItemName };
            if (dataset.gtagItemCategory) {
                item.item_category = dataset.gtagItemCategory;
            }
            if (dataset.gtagItemId) {
                item.item_id = dataset.gtagItemId;
            }
            payload.items = [...(payload.items || []), item];
        }
        if (dataset.gtagParams) {
            Object.assign(payload, parseJson(dataset.gtagParams));
        }
        return payload;
    };

    document.querySelectorAll('[data-gtag-load]').forEach((node) => {
        const payload = buildPayload(node, {
            event_category: node.dataset.gtagCategory || 'engagement',
            event_label: node.dataset.gtagLabel || window.location.pathname,
        });
        trackEvent(node.dataset.gtagLoad, payload);
    });

    document.querySelectorAll('[data-gtag-click]').forEach((el) => {
        el.addEventListener('click', () => {
            const payload = buildPayload(el, {
                event_category: el.dataset.gtagCategory || 'interaction',
                event_label: el.dataset.gtagLabel || el.textContent.trim(),
            });
            trackEvent(el.dataset.gtagClick, payload);
        });
    });

    document.querySelectorAll('[data-gtag-submit]').forEach((form) => {
        form.addEventListener('submit', () => {
            const payload = buildPayload(form, {
                event_category: form.dataset.gtagCategory || 'form',
                event_label:
                    form.dataset.gtagLabel ||
                    form.getAttribute('action') ||
                    window.location.pathname,
            });
            trackEvent(form.dataset.gtagSubmit, payload);
        });
    });

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

    const navBreakpoint = 900;
    const siteNavs = document.querySelectorAll('.site-header .nav');
    siteNavs.forEach((nav) => {
        const toggle = nav.querySelector('[data-nav-toggle]');
        const menu = nav.querySelector('[data-nav-menu]');
        if (!toggle || !menu) {
            return;
        }
        const closeMenu = () => {
            nav.classList.remove('is-open');
            toggle.classList.remove('is-active');
            toggle.setAttribute('aria-expanded', 'false');
        };
        toggle.addEventListener('click', () => {
            const isOpen = nav.classList.toggle('is-open');
            toggle.classList.toggle('is-active', isOpen);
            toggle.setAttribute('aria-expanded', String(isOpen));
        });
        menu.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= navBreakpoint && nav.classList.contains('is-open')) {
                    closeMenu();
                }
            });
        });
        window.addEventListener('resize', () => {
            if (window.innerWidth > navBreakpoint && nav.classList.contains('is-open')) {
                closeMenu();
            }
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && nav.classList.contains('is-open')) {
                closeMenu();
            }
        });
    });

    const logoTrigger = document.querySelector('[data-logo-edit-trigger]');
    const logoModal = document.querySelector('[data-logo-edit-modal]');
    if (logoTrigger && logoModal) {
        const closeButtons = logoModal.querySelectorAll('[data-logo-edit-close]');
        const toggleModal = (show) => {
            logoModal.classList.toggle('is-visible', show);
        };
        logoTrigger.addEventListener('click', () => toggleModal(true));
        closeButtons.forEach((btn) => btn.addEventListener('click', () => toggleModal(false)));
        logoModal.addEventListener('click', (event) => {
            if (event.target === logoModal) {
                toggleModal(false);
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

    const tokenButtons = document.querySelectorAll("[data-token-target]");
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

    const copyButtons = document.querySelectorAll("[data-copy-target]");
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

    const heroButtons = document.querySelectorAll(".persona-btn");
    const heroSubtitle = document.getElementById("heroSubtitle");
    const heroPrimary = document.getElementById("heroPrimaryCta");
    const heroSecondary = document.getElementById("heroSecondaryCta");
    const heroSection = document.querySelector(".hero");
    heroButtons.forEach((button) => {
        button.addEventListener("click", () => {
            heroButtons.forEach((btn) => btn.classList.remove("is-active"));
            button.classList.add("is-active");
            if (heroSubtitle) {
                heroSubtitle.textContent = button.dataset.subtitle || heroSubtitle.textContent;
            }
            if (heroPrimary) {
                heroPrimary.textContent = button.dataset.primary || heroPrimary.textContent;
                if (button.dataset.primaryLink) {
                    heroPrimary.setAttribute("href", button.dataset.primaryLink);
                }
            }
            if (heroSecondary) {
                heroSecondary.textContent = button.dataset.secondary || heroSecondary.textContent;
                if (button.dataset.secondaryLink) {
                    heroSecondary.setAttribute("href", button.dataset.secondaryLink);
                }
            }
            if (heroSection && button.dataset.persona) {
                heroSection.setAttribute("data-persona", button.dataset.persona);
            }
        });
    });

    const suiteButtons = document.querySelectorAll("[data-suite-button]");
    const suitePanels = document.querySelectorAll("[data-suite-panel]");
    suiteButtons.forEach((button) => {
        button.addEventListener("click", () => {
            suiteButtons.forEach((btn) => btn.classList.remove("is-active"));
            suitePanels.forEach((panel) => panel.classList.remove("is-active"));
            button.classList.add("is-active");
            suiteButtons.forEach((btn) => btn.setAttribute("aria-selected", "false"));
            button.setAttribute("aria-selected", "true");
            const target = button.dataset.target;
            const nextPanel = document.querySelector(`[data-suite-panel=\"${target}\"]`);
            if (nextPanel) {
                nextPanel.classList.add("is-active");
            }
        });
    });

    const liveFeedSlot = document.getElementById("liveFeedSlot");
    const liveFeedDataElem = document.getElementById("live-events-data");
    if (liveFeedSlot && liveFeedDataElem) {
        const events = JSON.parse(liveFeedDataElem.textContent);
        let eventIndex = 0;
        const renderEvent = () => {
            if (!events.length) {
                liveFeedSlot.textContent = "Teams worldwide are currently assessing with Evalon.";
                return;
            }
            const current = events[eventIndex];
            liveFeedSlot.innerHTML = `<span class="ticker-text">${current.company} launched a ${current.assessment} • ${current.ago}</span>`;
            eventIndex = (eventIndex + 1) % events.length;
        };
        renderEvent();
        setInterval(renderEvent, 4000);
    }

    const caseButtons = document.querySelectorAll("[data-case-button]");
    const casePanels = document.querySelectorAll("[data-case-panel]");
    if (caseButtons.length && casePanels.length) {
        const setCase = (index) => {
            caseButtons.forEach((btn, idx) => btn.classList.toggle("is-active", idx === index));
            casePanels.forEach((panel, idx) => panel.classList.toggle("is-active", idx === index));
        };
        caseButtons.forEach((button) => {
            button.addEventListener("click", () => setCase(Number(button.dataset.caseButton)));
        });
        let caseIndex = 0;
        setInterval(() => {
            caseIndex = (caseIndex + 1) % caseButtons.length;
            setCase(caseIndex);
        }, 6000);
    }

    const revealItems = document.querySelectorAll(".reveal");
    if (revealItems.length && "IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15 }
        );
        revealItems.forEach((el) => observer.observe(el));
    } else {
        revealItems.forEach((el) => el.classList.add("is-visible"));
    }

    const featuredSliders = document.querySelectorAll("[data-featured-slider]");
    featuredSliders.forEach((slider) => {
        const track = slider.querySelector("[data-slider-track]");
        const slides = slider.querySelectorAll("[data-slider-slide]");
        const prev = slider.querySelector("[data-slider-prev]");
        const next = slider.querySelector("[data-slider-next]");
        const indicators = slider.querySelectorAll("[data-slider-indicator]");
        if (!track || !slides.length) {
            return;
        }
        let index = 0;
        let autoplay;
        const setIndex = (nextIndex) => {
            if (!slides.length) {
                return;
            }
            const slideCount = slides.length;
            index = (nextIndex + slideCount) % slideCount;
            track.style.transform = `translateX(-${index * 100}%)`;
            indicators.forEach((dot, dotIndex) => {
                dot.classList.toggle("is-active", dotIndex === index);
            });
        };
        const startAutoplay = () => {
            if (autoplay) {
                clearInterval(autoplay);
            }
            autoplay = setInterval(() => setIndex(index + 1), 7000);
        };
        const stopAutoplay = () => autoplay && clearInterval(autoplay);
        prev?.addEventListener("click", () => {
            setIndex(index - 1);
            startAutoplay();
        });
        next?.addEventListener("click", () => {
            setIndex(index + 1);
            startAutoplay();
        });
        indicators.forEach((dot) => {
            dot.addEventListener("click", () => {
                const target = Number(dot.dataset.sliderIndicator);
                if (!Number.isNaN(target)) {
                    setIndex(target);
                    startAutoplay();
                }
            });
        });
        slider.addEventListener("mouseenter", stopAutoplay);
        slider.addEventListener("mouseleave", startAutoplay);
        setIndex(0);
        startAutoplay();
    });

    const blogFilterForms = document.querySelectorAll("[data-blog-filter-form]");
    blogFilterForms.forEach((form) => {
        const searchInput = form.querySelector("[data-blog-search-input]");
        const clearButton = form.querySelector("[data-clear-search]");
        let debounceTimer;
        if (searchInput) {
            const triggerSubmit = () => {
                if (typeof form.requestSubmit === "function") {
                    form.requestSubmit();
                } else {
                    form.submit();
                }
            };
            searchInput.addEventListener("input", () => {
                if (clearButton) {
                    clearButton.classList.toggle("is-hidden", !searchInput.value.length);
                }
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(triggerSubmit, 450);
            });
            searchInput.addEventListener("keydown", (event) => {
                if (event.key === "Enter") {
                    clearTimeout(debounceTimer);
                }
            });
        }
        if (clearButton && searchInput) {
            clearButton.addEventListener("click", () => {
                searchInput.value = "";
                clearButton.classList.add("is-hidden");
                if (typeof form.requestSubmit === "function") {
                    form.requestSubmit();
                } else {
                    form.submit();
                }
            });
        }
    });

    const spyNavs = document.querySelectorAll("[data-spy-nav]");
    spyNavs.forEach((nav) => {
        const links = Array.from(nav.querySelectorAll("a[href^='#']"));
        if (!links.length) {
            return;
        }
        const sections = links
            .map((link) => {
                const id = link.getAttribute("href").slice(1);
                const section = document.getElementById(id);
                return section ? { link, section } : null;
            })
            .filter(Boolean);
        if (!sections.length) {
            return;
        }
        let ticking = false;
        const activateCurrent = () => {
            const offset = 140;
            let activeEntry = sections[0];
            sections.forEach((entry) => {
                const rect = entry.section.getBoundingClientRect();
                if (rect.top - offset <= 0) {
                    activeEntry = entry;
                }
            });
            sections.forEach((entry) => {
                entry.link.classList.toggle("is-active", entry === activeEntry);
            });
        };
        const handleScroll = () => {
            if (ticking) {
                return;
            }
            ticking = true;
            window.requestAnimationFrame(() => {
                activateCurrent();
                ticking = false;
            });
        };
        window.addEventListener("scroll", handleScroll);
        window.addEventListener("resize", handleScroll);
        activateCurrent();
    });

    const playgroundDataElem = document.getElementById("playground-data");
    const playgroundContainer = document.querySelector("[data-playground]");
    if (playgroundDataElem && playgroundContainer) {
        let examples;
        try {
            examples = JSON.parse(playgroundDataElem.textContent);
        } catch (err) {
            examples = [];
        }
        if (examples.length) {
            const exampleMap = new Map(examples.map((example) => [example.slug, example]));
            const tabs = playgroundContainer.querySelectorAll("[data-playground-tab]");
            const methodEl = playgroundContainer.querySelector("[data-playground-method]");
            const pathEl = playgroundContainer.querySelector("[data-playground-path]");
            const headerEl = playgroundContainer.querySelector("[data-playground-headers]");
            const requestEl = playgroundContainer.querySelector("[data-playground-request]");
            const responseEl = playgroundContainer.querySelector("[data-playground-response]");
            const statusEl = playgroundContainer.querySelector("[data-playground-status]");
            const runButton = playgroundContainer.querySelector("[data-playground-run]");
            const responseCard = responseEl?.closest(".ap-playground-card");
            const formatJson = (value) => {
                if (value === null || typeof value === "undefined") {
                    return "—";
                }
                if (typeof value === "string") {
                    return value;
                }
                return JSON.stringify(value, null, 2);
            };
            let activeSlug = examples[0].slug;
            const renderExample = (slug) => {
                const example = exampleMap.get(slug);
                if (!example) {
                    return;
                }
                activeSlug = slug;
                if (methodEl) {
                    methodEl.textContent = example.method;
                }
                if (pathEl) {
                    pathEl.textContent = example.path;
                }
                if (headerEl) {
                    headerEl.textContent = formatJson(example.request.headers);
                }
                if (requestEl) {
                    requestEl.textContent = formatJson(example.request.body);
                }
                if (responseEl) {
                    responseEl.textContent = formatJson(example.response.body);
                }
                if (statusEl) {
                    statusEl.textContent = example.response.status;
                }
                tabs.forEach((tab) => {
                    const isActive = tab.dataset.playgroundTab === slug;
                    tab.classList.toggle("is-active", isActive);
                    tab.setAttribute("aria-selected", isActive ? "true" : "false");
                });
            };
            tabs.forEach((tab) => {
                tab.addEventListener("click", () => renderExample(tab.dataset.playgroundTab));
            });
            if (runButton && responseCard) {
                runButton.addEventListener("click", () => {
                    runButton.disabled = true;
                    runButton.textContent = "Running…";
                    responseCard.classList.add("is-running");
                    if (responseEl) {
                        responseEl.style.opacity = "0.3";
                    }
                    if (statusEl) {
                        statusEl.textContent = "…";
                    }
                    setTimeout(() => {
                        if (responseEl) {
                            responseEl.style.opacity = "1";
                        }
                        renderExample(activeSlug);
                        runButton.disabled = false;
                        runButton.textContent = "Run mock call";
                        responseCard.classList.remove("is-running");
                    }, 1200);
                });
            }
            renderExample(activeSlug);
        }
    }
    const articleBody = document.querySelector("[data-article-body]");
    if (articleBody) {
        const headings = articleBody.querySelectorAll("h2, h3");
        const tocList = document.querySelector("[data-article-toc]");
        const progressBar = document.querySelector("[data-reading-progress] span");
        if (headings.length && tocList) {
            headings.forEach((heading, index) => {
                const slug =
                    heading.id ||
                    `section-${index}-${heading.textContent
                        .toLowerCase()
                        .replace(/[^a-z0-9]+/g, "-")
                        .replace(/^-|-$/g, "")}`;
                heading.id = slug;
                const li = document.createElement("li");
                const link = document.createElement("a");
                link.href = `#${slug}`;
                link.textContent = heading.textContent.trim();
                link.addEventListener("click", (event) => {
                    event.preventDefault();
                    document.getElementById(slug)?.scrollIntoView({
                        behavior: "smooth",
                        block: "start",
                    });
                });
                li.appendChild(link);
                tocList.appendChild(li);
            });
            const tocLinks = tocList.querySelectorAll("a");
            const observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach((entry) => {
                        if (entry.isIntersecting) {
                            tocLinks.forEach((link) =>
                                link.classList.toggle(
                                    "is-active",
                                    link.getAttribute("href") === `#${entry.target.id}`
                                )
                            );
                        }
                    });
                },
                { rootMargin: "-40% 0px -50% 0px", threshold: 0 }
            );
            headings.forEach((heading) => observer.observe(heading));
        }
        if (progressBar) {
            const updateProgress = () => {
                const scrollTop = window.scrollY || window.pageYOffset;
                const docHeight =
                    articleBody.offsetHeight - window.innerHeight + 200;
                const progress =
                    docHeight > 0 ? Math.min(100, (scrollTop / docHeight) * 100) : 0;
                progressBar.style.width = `${progress}%`;
            };
            window.addEventListener("scroll", updateProgress);
            window.addEventListener("resize", updateProgress);
            updateProgress();
        }
    }

    const relatedSlider = document.querySelector("[data-related-slider]");
    if (relatedSlider) {
        const track = relatedSlider.querySelector("[data-related-track]");
        const slides = relatedSlider.querySelectorAll("[data-related-slide]");
        const prev = document.querySelector("[data-related-prev]");
        const next = document.querySelector("[data-related-next]");
        if (track && slides.length) {
            const getGap = () =>
                parseFloat(
                    getComputedStyle(track).columnGap || getComputedStyle(track).gap || 0
                );
            const slideWidth = () => slides[0].getBoundingClientRect().width + getGap();
            let index = 0;
            const setIndex = (nextIndex) => {
                const count = slides.length;
                if (!count) {
                    return;
                }
                index = (nextIndex + count) % count;
                track.style.transform = `translateX(-${index * slideWidth()}px)`;
            };
            prev?.addEventListener("click", () => setIndex(index - 1));
            next?.addEventListener("click", () => setIndex(index + 1));
            window.addEventListener("resize", () => setIndex(index));
            setIndex(0);
        }
    }

    const blogCards = document.querySelectorAll("[data-blog-card]");
    if (blogCards.length && "IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.2 }
        );
        blogCards.forEach((card) => observer.observe(card));
    } else {
        blogCards.forEach((card) => card.classList.add("is-visible"));
    }

    // Portal Sidebar Navigation
    const portalSidebar = document.getElementById("portal-sidebar");
    const sidebarToggle = document.getElementById("sidebar-toggle");
    const portalContainer = document.querySelector(".portal-container");

    if (sidebarToggle && portalSidebar && portalContainer) {
        // Toggle sidebar on mobile
        sidebarToggle.addEventListener("click", () => {
            const isOpen = portalSidebar.classList.toggle("is-open");
            portalContainer.classList.toggle("sidebar-open", isOpen);
            sidebarToggle.setAttribute("aria-expanded", String(isOpen));

            // Animate toggle button
            sidebarToggle.classList.toggle("is-active", isOpen);
        });

        // Close sidebar when clicking overlay (mobile)
        portalContainer.addEventListener("click", (event) => {
            if (
                window.innerWidth <= 1024 &&
                portalSidebar.classList.contains("is-open") &&
                event.target === portalContainer
            ) {
                portalSidebar.classList.remove("is-open");
                portalContainer.classList.remove("sidebar-open");
                sidebarToggle.classList.remove("is-active");
                sidebarToggle.setAttribute("aria-expanded", "false");
            }
        });

        // Close sidebar on ESC key
        document.addEventListener("keydown", (event) => {
            if (
                event.key === "Escape" &&
                portalSidebar.classList.contains("is-open") &&
                window.innerWidth <= 1024
            ) {
                portalSidebar.classList.remove("is-open");
                portalContainer.classList.remove("sidebar-open");
                sidebarToggle.classList.remove("is-active");
                sidebarToggle.setAttribute("aria-expanded", "false");
            }
        });

        // Close sidebar on window resize to desktop
        window.addEventListener("resize", () => {
            if (window.innerWidth > 1024 && portalSidebar.classList.contains("is-open")) {
                portalSidebar.classList.remove("is-open");
                portalContainer.classList.remove("sidebar-open");
                sidebarToggle.classList.remove("is-active");
                sidebarToggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    // Global Search Functionality
    const globalSearch = document.getElementById("global-search");
    const searchClear = document.getElementById("search-clear");
    const searchResults = document.getElementById("search-results");

    if (globalSearch && searchResults) {
        let searchTimeout;

        // Mock search data - in production, this would be an API call
        const searchableItems = {
            assessments: [
                { title: "Digital Marketing Assessment", type: "assessment", url: "/clients/assessments/" },
                { title: "Product Management Assessment", type: "assessment", url: "/clients/assessments/" },
                { title: "Behavioral Assessment", type: "assessment", url: "/clients/assessments/" },
            ],
            pages: [
                { title: "Dashboard", type: "page", url: "/clients/dashboard/" },
                { title: "Assessments", type: "page", url: "/clients/assessments/" },
                { title: "Projects", type: "page", url: "/clients/dashboard/projects/" },
                { title: "Analytics", type: "page", url: "/clients/analytics/" },
                { title: "Settings", type: "page", url: "/clients/settings/" },
            ]
        };

        globalSearch.addEventListener("input", (e) => {
            const query = e.target.value.trim();

            // Show/hide clear button
            if (query) {
                searchClear.style.display = "flex";
            } else {
                searchClear.style.display = "none";
                searchResults.style.display = "none";
                return;
            }

            // Show loading state
            searchResults.innerHTML = `
                <div class="search-results loading">
                    <div class="loading-spinner"></div>
                </div>
            `;
            searchResults.style.display = "block";

            // Debounce search
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 300);
        });

        searchClear.addEventListener("click", () => {
            globalSearch.value = "";
            searchClear.style.display = "none";
            searchResults.style.display = "none";
            globalSearch.focus();
        });

        // Search shortcut hint (⌘K / Ctrl K)
        const searchShortcut = document.getElementById("search-shortcut");
        if (searchShortcut) {
            // Show correct modifier for platform
            if (!/Mac|iPhone|iPad/.test(navigator.platform || '')) {
                searchShortcut.textContent = "Ctrl K";
            }
            globalSearch.addEventListener("focus", () => {
                searchShortcut.style.display = "none";
            });
            globalSearch.addEventListener("blur", () => {
                if (!globalSearch.value) {
                    searchShortcut.style.display = "";
                }
            });
        }

        function performSearch(query) {
            const lowercaseQuery = query.toLowerCase();
            const results = [];

            // Search in all categories
            Object.entries(searchableItems).forEach(([category, items]) => {
                items.forEach(item => {
                    if (item.title.toLowerCase().includes(lowercaseQuery)) {
                        results.push({ ...item, category });
                    }
                });
            });

            displayResults(results, query);
        }

        function displayResults(results, query) {
            if (results.length === 0) {
                searchResults.innerHTML = `
                    <div class="search-empty">
                        No results found for "${query}"
                    </div>
                `;
                searchResults.style.display = "block";
                return;
            }

            const html = results.map(item => {
                const icon = getIcon(item.type);
                const meta = getMetaLabel(item.type);

                return `
                    <a href="${item.url}" class="search-result-item fade-in">
                        <div class="search-result-icon">
                            ${icon}
                        </div>
                        <div class="search-result-content">
                            <p class="search-result-title">${item.title}</p>
                            <p class="search-result-meta">${meta}</p>
                        </div>
                    </a>
                `;
            }).join("");

            searchResults.innerHTML = html;
            searchResults.style.display = "block";
            searchResults.classList.remove('loading');
        }

        function getIcon(type) {
            const icons = {
                assessment: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>`,
                page: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>`,
                project: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>`,
            };
            return icons[type] || icons.page;
        }

        function getMetaLabel(type) {
            const labels = {
                assessment: "Assessment",
                page: "Page",
                project: "Project",
                candidate: "Candidate",
            };
            return labels[type] || "Result";
        }

        // Close search results when clicking outside
        document.addEventListener("click", (e) => {
            if (!globalSearch.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = "none";
            }
        });

        // Close search results on ESC key
        globalSearch.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                globalSearch.value = "";
                searchClear.style.display = "none";
                searchResults.style.display = "none";
                globalSearch.blur();
            }
        });
    }

    // Notification Center
    const notificationToggle = document.getElementById("notification-toggle");
    const notificationDropdown = document.getElementById("notification-dropdown");
    const notificationBadge = document.getElementById("notification-badge");
    const notificationList = document.getElementById("notification-list");
    const markAllRead = document.getElementById("mark-all-read");

    if (notificationToggle && notificationDropdown) {
        // Mock notification data - in production, this would come from an API
        let notifications = [
            {
                id: 1,
                title: "Assessment Completed",
                message: "John Doe completed the Digital Marketing Assessment",
                time: "5 minutes ago",
                unread: true,
                link: "/clients/dashboard/assessments/marketing/",
            },
            {
                id: 2,
                title: "New Invite Response",
                message: "Jane Smith started the Product Management Assessment",
                time: "1 hour ago",
                unread: true,
                link: "/clients/dashboard/assessments/product/",
            },
            {
                id: 3,
                title: "Project Updated",
                message: "Senior Developer role has 3 new candidates",
                time: "3 hours ago",
                unread: false,
                link: "/clients/dashboard/projects/",
            },
        ];

        // Update badge count
        function updateBadgeCount() {
            const unreadCount = notifications.filter(n => n.unread).length;
            if (unreadCount > 0) {
                notificationBadge.textContent = unreadCount;
                notificationBadge.style.display = "flex";
                notificationToggle.classList.add("has-notifications");
            } else {
                notificationBadge.style.display = "none";
                notificationToggle.classList.remove("has-notifications");
            }
        }

        // Render notifications
        function renderNotifications() {
            // Show loading state
            notificationList.classList.add('loading');
            notificationList.innerHTML = `
                <div class="loading-spinner"></div>
            `;

            // Simulate brief loading (in production, this would be an actual API call)
            setTimeout(() => {
                notificationList.classList.remove('loading');

                if (notifications.length === 0) {
                    notificationList.innerHTML = `
                        <div class="notification-empty fade-in">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.3; margin-bottom: 0.5rem; color: var(--navy);">
                                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                            </svg>
                            <p>No new notifications</p>
                        </div>
                    `;
                    return;
                }

                const html = notifications.map(notif => `
                    <div class="notification-item fade-in ${notif.unread ? 'unread' : ''}" data-id="${notif.id}">
                        <div class="notification-content">
                            <p class="notification-title">${notif.title}</p>
                            <p class="notification-message">${notif.message}</p>
                            <p class="notification-time">${notif.time}</p>
                        </div>
                    </div>
                `).join("");

                notificationList.innerHTML = html;

                // Add click handlers to notification items
                document.querySelectorAll(".notification-item").forEach(item => {
                    item.addEventListener("click", () => {
                        const id = parseInt(item.dataset.id);
                        const notif = notifications.find(n => n.id === id);
                        if (notif) {
                            notif.unread = false;
                            updateBadgeCount();
                            renderNotifications();
                            if (notif.link) {
                                window.location.href = notif.link;
                            }
                        }
                    });
                });

                updateBadgeCount();
            }, 200); // Brief delay to show loading state
        }

        // Toggle dropdown
        notificationToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            const isVisible = notificationDropdown.style.display === "block";
            notificationDropdown.style.display = isVisible ? "none" : "block";
            if (!isVisible) {
                renderNotifications();
            }
        });

        // Mark all as read
        if (markAllRead) {
            markAllRead.addEventListener("click", () => {
                notifications.forEach(n => n.unread = false);
                updateBadgeCount();
                renderNotifications();
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener("click", (e) => {
            if (!notificationToggle.contains(e.target) && !notificationDropdown.contains(e.target)) {
                notificationDropdown.style.display = "none";
            }
        });

        // Initialize badge count
        updateBadgeCount();
    }

    // ==================================================================
    // KEYBOARD SHORTCUTS - Phase 4
    // ==================================================================

    // Global keyboard shortcuts handler
    document.addEventListener('keydown', (e) => {
        // Cmd/Ctrl + K: Focus search
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            const globalSearch = document.getElementById('global-search');
            if (globalSearch) {
                globalSearch.focus();
                globalSearch.select();
            }
        }

        // Cmd/Ctrl + /: Toggle sidebar on mobile
        if ((e.metaKey || e.ctrlKey) && e.key === '/') {
            e.preventDefault();
            const sidebarToggle = document.getElementById('sidebar-toggle');
            if (sidebarToggle && window.innerWidth <= 1024) {
                sidebarToggle.click();
            }
        }

        // Cmd/Ctrl + B: Open notifications
        if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
            e.preventDefault();
            const notificationToggle = document.getElementById('notification-toggle');
            if (notificationToggle) {
                notificationToggle.click();
            }
        }

        // Cmd/Ctrl + 1-5: Navigate to pages
        if ((e.metaKey || e.ctrlKey) && e.key >= '1' && e.key <= '5') {
            e.preventDefault();
            const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
            const index = parseInt(e.key) - 1;
            if (navItems[index]) {
                window.location.href = navItems[index].href;
            }
        }

        // Escape: Close all overlays
        if (e.key === 'Escape') {
            // Close search results
            const searchResults = document.getElementById('search-results');
            if (searchResults && searchResults.style.display === 'block') {
                searchResults.style.display = 'none';
                const globalSearch = document.getElementById('global-search');
                if (globalSearch) {
                    globalSearch.value = '';
                    const searchClear = document.getElementById('search-clear');
                    if (searchClear) searchClear.style.display = 'none';
                }
            }

            // Close notification dropdown
            const notificationDropdown = document.getElementById('notification-dropdown');
            if (notificationDropdown && notificationDropdown.style.display === 'block') {
                notificationDropdown.style.display = 'none';
            }
        }
    });

    // Arrow key navigation in search results
    // Reuse globalSearch and searchResults from above
    if (globalSearch && searchResults) {
        let selectedIndex = -1;

        globalSearch.addEventListener('keydown', (e) => {
            if (searchResults.style.display !== 'block') return;

            const items = searchResults.querySelectorAll('.search-result-item');
            if (items.length === 0) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                updateSelectedItem(items, selectedIndex);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                updateSelectedItem(items, selectedIndex);
            } else if (e.key === 'Enter' && selectedIndex >= 0) {
                e.preventDefault();
                items[selectedIndex].click();
            }
        });

        function updateSelectedItem(items, index) {
            items.forEach((item, i) => {
                if (i === index) {
                    item.style.background = 'var(--portal-bg-active)';
                    item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                } else {
                    item.style.background = '';
                }
            });
        }

        // Reset selection when closing search
        globalSearch.addEventListener('input', () => {
            selectedIndex = -1;
        });
    }

    // Show keyboard shortcuts hint on first visit
    const hasSeenShortcutsHint = localStorage.getItem('hasSeenKeyboardShortcuts');
    if (!hasSeenShortcutsHint && globalSearch) {
        setTimeout(() => {
            const hint = document.createElement('div');
            hint.style.cssText = `
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                background: var(--navy);
                color: white;
                padding: 1rem 1.5rem;
                border-radius: var(--portal-radius-md);
                box-shadow: var(--portal-shadow-lg);
                font-size: 0.9rem;
                z-index: 1000;
                animation: fadeIn 0.4s ease-out;
            `;
            hint.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div>
                        <strong>Tip:</strong> Press <kbd style="background: rgba(255,255,255,0.2); padding: 0.25rem 0.5rem; border-radius: 4px; font-family: monospace;">Cmd+K</kbd> to quickly search
                    </div>
                    <button onclick="this.parentElement.parentElement.remove(); localStorage.setItem('hasSeenKeyboardShortcuts', 'true');" style="background: none; border: none; color: white; cursor: pointer; font-size: 1.25rem; padding: 0; line-height: 1;">&times;</button>
                </div>
            `;
            document.body.appendChild(hint);

            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (hint.parentElement) {
                    hint.style.animation = 'fadeOut 0.4s ease-out';
                    setTimeout(() => {
                        hint.remove();
                        localStorage.setItem('hasSeenKeyboardShortcuts', 'true');
                    }, 400);
                }
            }, 5000);
        }, 2000);
    }

    // Newsletter subscription form handler
    const newsletterForms = document.querySelectorAll('[data-newsletter-form]');
    newsletterForms.forEach((form) => {
        const messageEl = form.parentElement?.querySelector('[data-newsletter-message]');
        const submitBtn = form.querySelector('button[type="submit"]');
        const emailInput = form.querySelector('input[name="email"]');

        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            const email = emailInput?.value?.trim();
            if (!email) {
                showMessage('Please enter your email address.', false);
                return;
            }

            // Disable form during submission
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Subscribing...';
            }

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, source: 'footer' }),
                });

                const data = await response.json();

                if (data.success) {
                    showMessage(data.message, true);
                    form.style.display = 'none';
                } else {
                    showMessage(data.error || 'Something went wrong. Please try again.', false);
                }
            } catch (error) {
                showMessage('Connection error. Please try again.', false);
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Subscribe';
                }
            }
        });

        function showMessage(text, isSuccess) {
            if (messageEl) {
                messageEl.textContent = text;
                messageEl.style.display = 'block';
                messageEl.style.color = isSuccess ? '#10b981' : '#ef4444';
            }
        }
    });
});
