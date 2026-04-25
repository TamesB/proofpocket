from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountsTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        resp = self.client.post(
            reverse("accounts:signup"),
            data={
                "username": "alice",
                "password1": "SuperSecurePass123!",
                "password2": "SuperSecurePass123!",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(get_user_model().objects.filter(username="alice").exists())

        # Dashboard requires login; after signup we should be authenticated.
        dash = self.client.get(reverse("core:dashboard"))
        self.assertEqual(dash.status_code, 200)

