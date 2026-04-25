from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AttachmentForm, PurchaseForm
from .models import Attachment, Purchase
from reminders.services import ensure_default_rules_for_user, recompute_events_for_purchase


def _render(request: HttpRequest, full: str, partial: str, ctx: dict) -> HttpResponse:
    return render(request, partial if request.htmx else full, ctx)


@login_required
def purchase_list(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()
    soon = request.GET.get("soon") == "1"

    purchases = Purchase.objects.filter(user=request.user)
    if q:
        purchases = purchases.filter(Q(title__icontains=q) | Q(merchant__icontains=q))
    if soon:
        today = timezone.localdate()
        horizon = today + timezone.timedelta(days=30)
        purchases = purchases.filter(
            Q(return_until__range=(today, horizon))
            | Q(warranty_until__range=(today, horizon))
        )

    return _render(
        request,
        "purchases/purchase_list.html",
        "purchases/partials/purchase_list.html",
        {"purchases": purchases[:200], "q": q, "soon": soon},
    )


@login_required
def purchase_new(request: HttpRequest) -> HttpResponse:
    ensure_default_rules_for_user(request.user)
    if request.method == "POST":
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.user = request.user
            purchase.save()
            form.save_m2m()
            recompute_events_for_purchase(purchase)
            return redirect("purchases:detail", purchase_id=purchase.id)
    else:
        form = PurchaseForm(initial={"purchased_at": timezone.localdate(), "currency": "EUR"})

    return _render(
        request,
        "purchases/purchase_new.html",
        "purchases/partials/purchase_new.html",
        {"form": form},
    )


@login_required
def purchase_detail(request: HttpRequest, purchase_id: str) -> HttpResponse:
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)
    return _render(
        request,
        "purchases/purchase_detail.html",
        "purchases/partials/purchase_detail.html",
        {"purchase": purchase, "attach_form": AttachmentForm()},
    )


@login_required
def purchase_edit(request: HttpRequest, purchase_id: str) -> HttpResponse:
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)
    ensure_default_rules_for_user(request.user)

    if request.method == "POST":
        form = PurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            recompute_events_for_purchase(purchase)
            return redirect("purchases:detail", purchase_id=purchase.id)
    else:
        form = PurchaseForm(instance=purchase)

    return _render(
        request,
        "purchases/purchase_edit.html",
        "purchases/partials/purchase_edit.html",
        {"purchase": purchase, "form": form},
    )


@login_required
def purchase_delete(request: HttpRequest, purchase_id: str) -> HttpResponse:
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)
    if request.method != "POST":
        raise Http404()
    purchase.delete()
    if request.htmx:
        # When deleting from an HTMX context, go back to list partial.
        return redirect("purchases:list")
    return redirect("purchases:list")


@login_required
def attachment_add(request: HttpRequest, purchase_id: str) -> HttpResponse:
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)
    if request.method != "POST":
        raise Http404()

    form = AttachmentForm(request.POST, request.FILES)
    if form.is_valid():
        attachment: Attachment = form.save(commit=False)
        attachment.purchase = purchase
        attachment.save()
        return redirect("purchases:detail", purchase_id=purchase.id)

    # On error, re-render detail with errors.
    return _render(
        request,
        "purchases/purchase_detail.html",
        "purchases/partials/purchase_detail.html",
        {"purchase": purchase, "attach_form": form},
    )
