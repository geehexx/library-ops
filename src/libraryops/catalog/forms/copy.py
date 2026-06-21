# pyright: reportMissingTypeArgument=false, reportUnknownMemberType=false
"""Copy form for catalog create and update flows."""

from __future__ import annotations

from typing import Any, cast

from django import forms
from django.contrib.auth.models import User

from libraryops.catalog import selectors
from libraryops.inventory.models import BookCopy, BookCopyStatus


class CopyForm(forms.ModelForm):
    """Collect copy metadata for create and update flows."""

    edition = forms.ModelChoiceField(queryset=selectors.edition_list(), label="Edition")
    status = forms.ChoiceField(choices=BookCopyStatus.choices, initial=BookCopyStatus.AVAILABLE)

    class Meta:
        """Bind the form to the inventory copy model."""

        model = BookCopy
        fields = ("edition", "barcode", "status", "shelf_location", "condition_note")
        labels = {
            "edition": "Edition",
            "barcode": "Barcode",
            "status": "Status",
            "shelf_location": "Shelf location",
            "condition_note": "Condition note",
        }
        widgets = {"condition_note": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Refresh relation querysets when rendering or binding the form."""

        super().__init__(*args, **kwargs)
        edition_field = self.fields["edition"]
        if not isinstance(edition_field, forms.ModelChoiceField):
            raise TypeError("Expected edition to be a model choice field.")
        edition_field.queryset = selectors.edition_list()

    def apply(self, *, actor: User) -> BookCopy:
        """Persist the copy through the owning manager."""

        edition = self.cleaned_data["edition"]
        barcode = str(self.cleaned_data["barcode"])
        status = self.cleaned_data["status"]
        shelf_location = str(self.cleaned_data["shelf_location"])
        condition_note = str(self.cleaned_data["condition_note"])
        copy = _bound_copy(self)
        if copy.pk:
            return BookCopy.objects.update_copy(
                actor=actor,
                copy=copy,
                edition=edition,
                barcode=barcode,
                status=status,
                shelf_location=shelf_location,
                condition_note=condition_note,
            )
        return BookCopy.objects.create_copy(
            actor=actor,
            edition=edition,
            barcode=barcode,
            status=status,
            shelf_location=shelf_location,
            condition_note=condition_note,
        )

    def archive(self, *, actor: User) -> BookCopy:
        """Archive the bound copy through the owning manager."""

        copy = _bound_copy(self)
        if not copy.pk:
            raise ValueError("Cannot archive an unsaved copy.")
        return BookCopy.objects.archive_copy(actor=actor, copy=copy)


def _bound_copy(form: CopyForm) -> BookCopy:
    """Return the form's bound copy instance through a narrow boundary cast."""

    return cast(BookCopy, form.instance)
