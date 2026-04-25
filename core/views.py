from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    template = "core/partials/dashboard.html" if request.htmx else "core/dashboard.html"
    return render(request, template)
