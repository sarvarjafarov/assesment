from django.db import models


class SiteContentBlock(models.Model):
    PAGE_HOME = "home"
    PAGE_BLOG = "blog"
    PAGE_CONTACT = "contact"
    PAGE_CAREERS = "careers"
    PAGE_SECURITY = "security"
    PAGE_PRIVACY = "privacy"
    PAGE_TERMS = "terms"
    PAGE_RESOURCES = "resources"
    PAGE_CHOICES = [
        (PAGE_HOME, "Homepage"),
        (PAGE_BLOG, "Blog"),
        (PAGE_CONTACT, "Contact"),
        (PAGE_CAREERS, "Careers"),
        (PAGE_SECURITY, "Security"),
        (PAGE_PRIVACY, "Privacy"),
        (PAGE_TERMS, "Terms"),
        (PAGE_RESOURCES, "Resources"),
    ]

    SLOT_HERO = "hero"
    SLOT_PAGE_HERO = "page_hero"
    SLOT_PAGE_SECTION = "page_section"
    SLOT_SUITE_HEADING = "suite_heading"
    SLOT_SUITE = "suite_card"
    SLOT_FEATURE = "feature_card"
    SLOT_TESTIMONIAL = "testimonial"
    SLOT_CHOICES = [
        (SLOT_HERO, "Hero"),
        (SLOT_PAGE_HERO, "Page hero"),
        (SLOT_PAGE_SECTION, "Page section"),
        (SLOT_SUITE_HEADING, "Assessment section heading"),
        (SLOT_SUITE, "Assessment card"),
        (SLOT_FEATURE, "Feature panel"),
        (SLOT_TESTIMONIAL, "Testimonial"),
    ]

    page = models.CharField(max_length=32, choices=PAGE_CHOICES, default=PAGE_HOME)
    slot = models.CharField(max_length=32, choices=SLOT_CHOICES, default=SLOT_FEATURE)
    title = models.CharField(max_length=220)
    subtitle = models.CharField(max_length=220, blank=True)
    body = models.TextField(blank=True)
    badge = models.CharField(max_length=120, blank=True)
    cta_label = models.CharField(max_length=120, blank=True)
    cta_url = models.URLField(blank=True)
    secondary_cta_label = models.CharField(max_length=120, blank=True)
    secondary_cta_url = models.URLField(blank=True)
    list_items = models.TextField(
        blank=True,
        help_text="For bullet lists. Enter one item per line.",
    )
    meta_items = models.TextField(
        blank=True,
        help_text="Optional key/value pairs. Format: Label | Value per line.",
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("page", "slot", "order")

    def __str__(self):
        return f"{self.get_page_display()} · {self.get_slot_display()} · {self.title}"

    def list_values(self) -> list[str]:
        return [line.strip() for line in self.list_items.splitlines() if line.strip()]

    def meta_pairs(self) -> list[dict]:
        pairs = []
        for line in self.meta_items.splitlines():
            line = line.strip()
            if not line:
                continue
            if "|" in line:
                label, value = line.split("|", 1)
            elif ":" in line:
                label, value = line.split(":", 1)
            else:
                label, value = line, ""
            pairs.append({"label": label.strip(), "value": value.strip()})
        return pairs


class ResourceAsset(models.Model):
    CATEGORY_GUIDE = "guide"
    CATEGORY_TEMPLATE = "template"
    CATEGORY_TOOLKIT = "toolkit"
    CATEGORY_CHOICES = [
        (CATEGORY_GUIDE, "Guide"),
        (CATEGORY_TEMPLATE, "Template"),
        (CATEGORY_TOOLKIT, "Toolkit"),
    ]

    title = models.CharField(max_length=220)
    summary = models.TextField()
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    file = models.FileField(upload_to="resources/")
    external_url = models.URLField(blank=True)
    version = models.CharField(max_length=40, blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "title")

    def __str__(self):
        return self.title

    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
