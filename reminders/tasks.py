from __future__ import annotations

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .email import send_via_resend
from .models import ReminderEvent, ReminderStatus


@shared_task
def enqueue_due_reminders(batch_size: int = 50) -> int:
    now = timezone.now()
    due_ids = list(
        ReminderEvent.objects.filter(status=ReminderStatus.PENDING, send_at__lte=now)
        .order_by("send_at")
        .values_list("id", flat=True)[:batch_size]
    )
    for event_id in due_ids:
        send_reminder_event.delay(event_id)
    return len(due_ids)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_reminder_event(self, event_id: int) -> None:
    with transaction.atomic():
        event = (
            ReminderEvent.objects.select_for_update()
            .select_related("purchase", "purchase__user")
            .get(id=event_id)
        )
        if event.status != ReminderStatus.PENDING:
            return

        user = event.purchase.user
        to_email = getattr(user, "email", "") or ""
        if not to_email:
            event.status = ReminderStatus.SKIPPED
            event.last_error = "User has no email address"
            event.save(update_fields=["status", "last_error"])
            return

        subject = f"ProofPocket reminder: {event.purchase.title}"
        html = f"""
        <div style="font-family: ui-sans-serif, system-ui; line-height: 1.5;">
          <h2 style="margin: 0 0 12px;">Reminder</h2>
          <p style="margin: 0 0 8px;">
            <strong>{event.purchase.title}</strong>
          </p>
          <p style="margin: 0 0 8px;">
            Type: <strong>{event.get_kind_display()}</strong>
          </p>
          <p style="margin: 0 0 8px;">
            Purchased: {event.purchase.purchased_at}
          </p>
          <p style="margin: 0;">
            Open your dashboard for details.
          </p>
        </div>
        """.strip()

        result = send_via_resend(to_email=to_email, subject=subject, html=html)
        if result.ok:
            event.status = ReminderStatus.SENT
            event.sent_at = timezone.now()
            event.last_error = ""
            event.save(update_fields=["status", "sent_at", "last_error"])
            return

        event.status = ReminderStatus.FAILED
        event.last_error = result.error or "Unknown error"
        event.save(update_fields=["status", "last_error"])

