from __future__ import annotations

import json

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


def normalize_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def update_session_telemetry(session, *, request=None, payload: dict | str | None = None):
    telemetry = dict(session.telemetry_log or {})
    changed = False

    if request is not None:
        ip_address = normalize_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        device = telemetry.get("device_info") or {}
        if ip_address and not device.get("ip"):
            device["ip"] = ip_address
            changed = True
        if user_agent and not device.get("user_agent"):
            device["user_agent"] = user_agent[:500]
            changed = True
        if device and "first_seen" not in device:
            device["first_seen"] = timezone.now().isoformat()
            changed = True
        if device:
            telemetry["device_info"] = device
        if ip_address:
            history = telemetry.get("ip_history") or []
            if ip_address not in history:
                history.append(ip_address)
                telemetry["ip_history"] = history
                changed = True

    if payload:
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (ValueError, TypeError):
                payload = None
        if isinstance(payload, dict):
            events = telemetry.get("events") or []
            events.append(
                {
                    "timestamp": timezone.now().isoformat(),
                    "data": payload,
                }
            )
            telemetry["events"] = events
            paste_count = payload.get("pasteCount")
            if isinstance(paste_count, int):
                telemetry["paste_count"] = max(
                    paste_count, telemetry.get("paste_count") or 0
                )
            device_hints = payload.get("deviceHints") or {}
            if device_hints:
                existing_hints = telemetry.get("device_hints") or {}
                existing_hints.update(device_hints)
                telemetry["device_hints"] = existing_hints
            changed = True

    if changed:
        session.telemetry_log = telemetry
        session.save(update_fields=["telemetry_log", "updated_at"])


def send_switch_device_email(
    *,
    email: str | None,
    candidate_name: str | None,
    resume_link: str,
    assessment_label: str,
) -> tuple[bool, str | None]:
    """
    Send a lightweight email that lets a candidate resume the assessment on another device.

    Returns a tuple of (success, error_message). The caller is responsible for displaying
    any messaging to the user based on the return payload.
    """

    if not email:
        return False, "We do not have an email address on file for this session."
    if not settings.EMAIL_ENABLED:
        return False, "Email delivery is currently disabled on this environment."

    subject = f"{assessment_label} assessment link"
    display_name = candidate_name or "there"
    body = (
        f"Hi {display_name},\n\n"
        "You asked us to send your secure assessment link so you can continue on another device.\n"
        f"Open the link below from your preferred browser:\n\n{resume_link}\n\n"
        "If you did not request this email, you can safely ignore it.\n\n"
        "— Evalon Assessments"
    )

    try:
        send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
            [email],
        )
    except Exception as exc:  # pragma: no cover - network configuration/runtime dependent
        return False, str(exc)
    return True, None


def notify_support_team(subject: str, body: str) -> bool:
    """Best-effort email notification for urgent candidate support requests."""
    recipient = getattr(
        settings,
        "SUPPORT_CONTACT_EMAIL",
        getattr(settings, "SUPPORT_INBOX", None),
    )
    if not recipient:
        return False
    if not getattr(settings, "EMAIL_ENABLED", False):
        return False
    try:
        send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
            [recipient],
        )
    except Exception:  # pragma: no cover - email backend dependent
        return False
    return True
