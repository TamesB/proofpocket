from django.conf import settings
from django.db import models
from django.utils import timezone

from purchases.models import Purchase


class ReminderKind(models.TextChoices):
    RETURN = "return", "Return window"
    WARRANTY = "warranty", "Warranty"


class ReminderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class ReminderRule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=16, choices=ReminderKind.choices)
    days_before = models.PositiveSmallIntegerField()
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "kind", "days_before"], name="uniq_rule_user_kind_days"
            )
        ]
        ordering = ["kind", "days_before"]

    def __str__(self) -> str:
        return f"{self.user_id} {self.kind} {self.days_before}d"


class ReminderEvent(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="reminder_events")
    kind = models.CharField(max_length=16, choices=ReminderKind.choices)
    send_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=ReminderStatus.choices, default=ReminderStatus.PENDING)
    last_error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["purchase", "kind", "send_at"], name="uniq_event_purchase_kind_send_at"
            )
        ]
        ordering = ["send_at"]

    @property
    def is_due(self) -> bool:
        return self.status == ReminderStatus.PENDING and self.send_at <= timezone.now()
