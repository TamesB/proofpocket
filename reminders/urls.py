from django.urls import path

from . import views

app_name = "reminders"

urlpatterns = [
    path("settings/", views.reminder_settings, name="settings"),
]

