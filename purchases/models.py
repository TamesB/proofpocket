import uuid

from django.conf import settings
from django.db import models


class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="uniq_tag_user_name")
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Purchase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=120)
    merchant = models.CharField(max_length=120, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="EUR")

    purchased_at = models.DateField()
    return_until = models.DateField(null=True, blank=True)
    warranty_until = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="purchases")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-purchased_at", "-created_at"]

    def __str__(self) -> str:
        return self.title


class AttachmentKind(models.TextChoices):
    RECEIPT = "receipt", "Receipt"
    WARRANTY = "warranty", "Warranty"
    MANUAL = "manual", "Manual"


def purchase_attachment_path(instance: "Attachment", filename: str) -> str:
    return f"users/{instance.purchase.user_id}/purchases/{instance.purchase_id}/{filename}"


class Attachment(models.Model):
    purchase = models.ForeignKey(
        Purchase, on_delete=models.CASCADE, related_name="attachments"
    )
    kind = models.CharField(max_length=16, choices=AttachmentKind.choices)
    file = models.FileField(upload_to=purchase_attachment_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.kind} ({self.file.name})"
