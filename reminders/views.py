from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .models import ReminderRule
from .services import ensure_default_rules_for_user


@login_required
def reminder_settings(request: HttpRequest) -> HttpResponse:
    ensure_default_rules_for_user(request.user)

    if request.method == "POST":
        # Simple MVP: toggle existing rules on/off
        enabled_ids = set(request.POST.getlist("enabled_rule"))
        for rule in ReminderRule.objects.filter(user=request.user):
            rule.enabled = str(rule.id) in enabled_ids
            rule.save(update_fields=["enabled"])
        return redirect("reminders:settings")

    rules = ReminderRule.objects.filter(user=request.user)
    template = (
        "reminders/partials/settings.html" if request.htmx else "reminders/settings.html"
    )
    return render(request, template, {"rules": rules})

from django.shortcuts import render

# Create your views here.
