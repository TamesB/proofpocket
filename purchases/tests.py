import tempfile
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from reminders.models import ReminderEvent, ReminderKind

from .models import Attachment, AttachmentKind, Purchase


TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="proofpocket-test-media-")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PurchasesFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="bob", password="pass12345", email="bob@example.com"
        )
        self.client.force_login(self.user)

    def test_create_purchase_schedules_default_events(self):
        today = timezone.localdate()
        warranty_until = today + timedelta(days=10)

        resp = self.client.post(
            reverse("purchases:new"),
            data={
                "title": "Headphones",
                "merchant": "Shop",
                "price": "99.99",
                "currency": "EUR",
                "purchased_at": today.isoformat(),
                "warranty_until": warranty_until.isoformat(),
                "return_until": "",
                "notes": "Keep box",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)

        purchase = Purchase.objects.get(user=self.user, title="Headphones")
        # Default rules include 7 days before; with warranty_until set, we should get a warranty event.
        self.assertTrue(
            ReminderEvent.objects.filter(
                purchase=purchase, kind=ReminderKind.WARRANTY
            ).exists()
        )

    def test_list_search_filters(self):
        Purchase.objects.create(
            user=self.user,
            title="Phone",
            merchant="Apple",
            price="1.00",
            currency="EUR",
            purchased_at=date.today(),
        )
        Purchase.objects.create(
            user=self.user,
            title="Laptop",
            merchant="Dell",
            price="2.00",
            currency="EUR",
            purchased_at=date.today(),
        )

        resp = self.client.get(reverse("purchases:list"), {"q": "Dell"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Laptop")
        self.assertNotContains(resp, "Phone")

    def test_attachment_upload(self):
        p = Purchase.objects.create(
            user=self.user,
            title="Camera",
            merchant="Store",
            price="10.00",
            currency="EUR",
            purchased_at=date.today(),
        )
        upload = SimpleUploadedFile("receipt.txt", b"hello", content_type="text/plain")

        resp = self.client.post(
            reverse("purchases:attachment_add", kwargs={"purchase_id": p.id}),
            data={"kind": AttachmentKind.RECEIPT, "file": upload},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Attachment.objects.filter(purchase=p, kind=AttachmentKind.RECEIPT).exists())

    def test_cannot_access_other_users_purchase(self):
        other = get_user_model().objects.create_user(
            username="eve", password="pass12345", email="eve@example.com"
        )
        p = Purchase.objects.create(
            user=other,
            title="Secret",
            merchant="X",
            price="1.00",
            currency="EUR",
            purchased_at=date.today(),
        )
        resp = self.client.get(reverse("purchases:detail", kwargs={"purchase_id": p.id}))
        self.assertEqual(resp.status_code, 404)


def tearDownModule():
    # Best-effort cleanup of temp upload folder
    import shutil

    shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

