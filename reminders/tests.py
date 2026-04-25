from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from purchases.models import Purchase

from .models import ReminderEvent, ReminderRule, ReminderStatus
from .services import ensure_default_rules_for_user, recompute_events_for_purchase
from .tasks import enqueue_due_reminders, send_reminder_event


class ReminderDomainTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="r1", password="pass12345", email="r1@example.com"
        )
        self.client.force_login(self.user)

    def test_default_rules_created(self):
        ensure_default_rules_for_user(self.user)
        self.assertGreaterEqual(ReminderRule.objects.filter(user=self.user).count(), 2)

    def test_recompute_creates_events_for_deadlines(self):
        ensure_default_rules_for_user(self.user)
        today = timezone.localdate()
        p = Purchase.objects.create(
            user=self.user,
            title="TV",
            merchant="Shop",
            price="1.00",
            currency="EUR",
            purchased_at=today,
            warranty_until=today + timedelta(days=10),
        )
        recompute_events_for_purchase(p)
        self.assertTrue(ReminderEvent.objects.filter(purchase=p).exists())

    def test_settings_toggle_updates_enabled_flags(self):
        ensure_default_rules_for_user(self.user)
        rules = list(ReminderRule.objects.filter(user=self.user))
        self.assertTrue(any(r.enabled for r in rules))

        # Disable all
        resp = self.client.post(reverse("reminders:settings"), data={}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ReminderRule.objects.filter(user=self.user, enabled=True).exists())


class ReminderTaskTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="r2", password="pass12345", email="r2@example.com"
        )
        self.client.force_login(self.user)

    def test_enqueue_due_reminders_calls_delay(self):
        p = Purchase.objects.create(
            user=self.user,
            title="Mouse",
            merchant="Shop",
            price="1.00",
            currency="EUR",
            purchased_at=timezone.localdate(),
        )
        event = ReminderEvent.objects.create(
            purchase=p,
            kind="warranty",
            send_at=timezone.now() - timedelta(minutes=1),
        )

        with patch("reminders.tasks.send_reminder_event.delay") as delay_mock:
            n = enqueue_due_reminders(batch_size=10)
            self.assertEqual(n, 1)
            delay_mock.assert_called_once_with(event.id)

    def test_send_reminder_event_marks_sent(self):
        p = Purchase.objects.create(
            user=self.user,
            title="Keyboard",
            merchant="Shop",
            price="1.00",
            currency="EUR",
            purchased_at=timezone.localdate(),
        )
        event = ReminderEvent.objects.create(
            purchase=p,
            kind="return",
            send_at=timezone.now() - timedelta(minutes=1),
        )

        with patch("reminders.tasks.send_via_resend") as send_mock:
            send_mock.return_value.ok = True
            send_mock.return_value.error = None
            send_mock.return_value.message_id = "id"

            send_reminder_event(event.id)

        event.refresh_from_db()
        self.assertEqual(event.status, ReminderStatus.SENT)
        self.assertIsNotNone(event.sent_at)

    def test_send_reminder_event_marks_skipped_without_email(self):
        user2 = get_user_model().objects.create_user(username="noemail", password="pass12345")
        p = Purchase.objects.create(
            user=user2,
            title="Cable",
            merchant="Shop",
            price="1.00",
            currency="EUR",
            purchased_at=timezone.localdate(),
        )
        event = ReminderEvent.objects.create(
            purchase=p,
            kind="return",
            send_at=timezone.now() - timedelta(minutes=1),
        )

        send_reminder_event(event.id)
        event.refresh_from_db()
        self.assertEqual(event.status, ReminderStatus.SKIPPED)
