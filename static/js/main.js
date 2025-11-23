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
            const responseCard = responseEl?.closest(".playground-card");
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
                    setTimeout(() => {
                        renderExample(activeSlug);
                        runButton.disabled = false;
                        runButton.textContent = "Run mock call";
                        responseCard.classList.remove("is-running");
                    }, 700);
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
});
