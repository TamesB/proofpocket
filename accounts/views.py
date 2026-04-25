from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render


def signup(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("core:dashboard")
    else:
        form = UserCreationForm()
        for field_name in ["username", "password1", "password2"]:
            form.fields[field_name].widget.attrs.setdefault(
                "class",
                "w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100",
            )
    return render(request, "accounts/signup.html", {"form": form})
