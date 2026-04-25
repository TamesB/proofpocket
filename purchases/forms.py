from django import forms

from .models import Attachment, Purchase


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = [
            "title",
            "merchant",
            "price",
            "currency",
            "purchased_at",
            "return_until",
            "warranty_until",
            "notes",
        ]
        widgets = {
            "purchased_at": forms.DateInput(attrs={"type": "date"}),
            "return_until": forms.DateInput(attrs={"type": "date"}),
            "warranty_until": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base = (
            "w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm "
            "text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-2 "
            "focus:ring-zinc-500/40"
        )
        for name, field in self.fields.items():
            if name == "notes":
                field.widget.attrs.setdefault("class", base)
            else:
                field.widget.attrs.setdefault("class", base)


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ["kind", "file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["kind"].widget.attrs.setdefault(
            "class",
            "w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100",
        )
        self.fields["file"].widget.attrs.setdefault(
            "class",
            "w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100",
        )

