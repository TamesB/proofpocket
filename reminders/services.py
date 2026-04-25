from __future__ import annotations

from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from purchases.models import Purchase

from .models import ReminderEvent, ReminderKind, ReminderRule, ReminderStatus


def _deadline_for_kind(purchase: Purchase, kind: str):
    if kind == ReminderKind.RETURN:
        return purchase.return_until
    if kind == ReminderKind.WARRANTY:
        return purchase.warranty_until
    return None


def _send_at_for_deadline(deadline_date, days_before: int) -> datetime:
    # Normalize to local midnight to keep it simple/predictable.
    local_midnight = datetime.combine(deadline_date - timedelta(days=days_before), time(9, 0))
    return timezone.make_aware(local_midnight)


@transaction.atomic
def recompute_events_for_purchase(purchase: Purchase) -> None:
    rules = ReminderRule.objects.filter(user=purchase.user, enabled=True)

    desired = set()
    for rule in rules:
        deadline = _deadline_for_kind(purchase, rule.kind)
        if not deadline:
            continue
        send_at = _send_at_for_deadline(deadline, rule.days_before)
        desired.add((rule.kind, send_at))

    existing = {
        (e.kind, e.send_at): e
        for e in ReminderEvent.objects.select_for_update().filter(purchase=purchase)
    }

    # Delete pending events that are no longer desired.
    for key, ev in existing.items():
        if key not in desired and ev.status == ReminderStatus.PENDING:
            ev.delete()

    # Ensure all desired events exist.
    for kind, send_at in desired:
        if (kind, send_at) in existing:
            continue
        ReminderEvent.objects.create(purchase=purchase, kind=kind, send_at=send_at)


def ensure_default_rules_for_user(user) -> None:
    defaults = [
        (ReminderKind.RETURN, 7),
        (ReminderKind.WARRANTY, 7),
    ]
    for kind, days_before in defaults:
        ReminderRule.objects.get_or_create(
            user=user, kind=kind, days_before=days_before, defaults={"enabled": True}
        )
