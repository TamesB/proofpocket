from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings


@dataclass(frozen=True)
class SendEmailResult:
    ok: bool
    message_id: str | None = None
    error: str | None = None


def send_via_resend(*, to_email: str, subject: str, html: str) -> SendEmailResult:
    if not settings.RESEND_API_KEY:
        return SendEmailResult(ok=False, error="RESEND_API_KEY is not set")

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
        json={
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html,
        },
        timeout=20,
    )

    if 200 <= resp.status_code < 300:
        data = resp.json() if resp.content else {}
        return SendEmailResult(ok=True, message_id=data.get("id"))

    try:
        err = resp.json()
    except Exception:
        err = resp.text
    return SendEmailResult(ok=False, error=f"{resp.status_code}: {err}")

