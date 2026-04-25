from django.urls import path

from . import views

app_name = "purchases"

urlpatterns = [
    path("", views.purchase_list, name="list"),
    path("new/", views.purchase_new, name="new"),
    path("<uuid:purchase_id>/", views.purchase_detail, name="detail"),
    path("<uuid:purchase_id>/edit/", views.purchase_edit, name="edit"),
    path("<uuid:purchase_id>/delete/", views.purchase_delete, name="delete"),
    path("<uuid:purchase_id>/attachments/add/", views.attachment_add, name="attachment_add"),
]

