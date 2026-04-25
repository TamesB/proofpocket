from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class CoreTests(TestCase):
    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse("core:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

    def test_dashboard_renders_for_logged_in_user(self):
        user = get_user_model().objects.create_user(username="u1", password="pass12345")
        self.client.force_login(user)

        resp = self.client.get(reverse("core:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Dashboard")

