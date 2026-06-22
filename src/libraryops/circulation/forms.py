"""Circulation workflow forms for checkout and return actions."""

from __future__ import annotations

from typing import Any

from django import forms
from django.contrib.auth.models import User

from libraryops.circulation.models import Loan
from libraryops.circulation.selectors import (
    borrower_label,
    checkout_borrower_queryset,
    checkout_copy_queryset,
    copy_label,
    loan_label,
    return_loan_queryset,
)
from libraryops.inventory.models import BookCopy


class _SearchSelectField(forms.ModelChoiceField):  # pyright: ignore[reportMissingTypeArgument]
    """Render a searchable select with stable, human-facing option labels."""

    def __init__(
        self,
        *,
        queryset: Any,
        option_label: Any,
        **kwargs: Any,
    ) -> None:
        self._option_label = option_label
        super().__init__(queryset=queryset, **kwargs)  # pyright: ignore[reportUnknownMemberType]

    def label_from_instance(self, obj: Any) -> str:
        """Return the display label for one option."""

        return str(self._option_label(obj))

    def set_queryset(self, queryset: Any) -> None:
        """Replace the backing queryset used to build the select options."""

        self.queryset = queryset


class CheckoutForm(forms.Form):
    """Collect the data needed to checkout one available copy."""

    copy = _SearchSelectField(
        queryset=BookCopy.objects.none(),
        option_label=copy_label,
        label="Copy",
        empty_label="Choose a copy",
        help_text="Search above by barcode or title, then choose an available copy.",
    )
    borrower = _SearchSelectField(
        queryset=User.objects.none(),
        option_label=borrower_label,
        label="Borrower",
        empty_label="Choose a borrower",
        help_text="Search above by borrower name or patron code, then choose a borrower.",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Refresh the dynamic querysets used by the workflow."""

        super().__init__(*args, **kwargs)
        self.copy_query = self._lookup_query("copy_query")
        self.borrower_query = self._lookup_query("borrower_query")

        copy_field = self.fields["copy"]
        if not isinstance(copy_field, _SearchSelectField):
            raise TypeError("Expected copy to use the searchable select field.")
        copy_field.set_queryset(checkout_copy_queryset(query=self.copy_query))
        copy_field.widget.attrs["autofocus"] = "autofocus"

        borrower_field = self.fields["borrower"]
        if not isinstance(borrower_field, _SearchSelectField):
            raise TypeError("Expected borrower to use the searchable select field.")
        borrower_field.set_queryset(checkout_borrower_queryset(query=self.borrower_query))

    def _lookup_query(self, key: str) -> str:
        """Return one preserved search query for the rendered controls."""

        value = self.initial.get(key, "")
        return str(value or "").strip()

    def apply(self, *, actor: User) -> Loan:
        """Persist the checkout through the loan manager."""

        copy = self.cleaned_data["copy"]
        if not isinstance(copy, BookCopy):
            raise TypeError("Expected cleaned copy to be a BookCopy.")
        borrower = self.cleaned_data["borrower"]
        if not isinstance(borrower, User):
            raise TypeError("Expected cleaned borrower to be a User.")
        return Loan.objects.checkout_copy(actor=actor, copy=copy, borrower=borrower)


class ReturnForm(forms.Form):
    """Collect the data needed to return one active loan."""

    loan = _SearchSelectField(
        queryset=Loan.objects.none(),
        option_label=loan_label,
        label="Loan",
        empty_label="Choose an active loan",
        help_text="Search above by barcode, title, borrower name, or patron code.",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Refresh the dynamic loan queryset used by the workflow."""

        super().__init__(*args, **kwargs)
        self.loan_query = self._lookup_query("loan_query")

        loan_field = self.fields["loan"]
        if not isinstance(loan_field, _SearchSelectField):
            raise TypeError("Expected loan to use the searchable select field.")
        loan_field.set_queryset(return_loan_queryset(query=self.loan_query))
        loan_field.widget.attrs["autofocus"] = "autofocus"

    def _lookup_query(self, key: str) -> str:
        """Return one preserved search query for the rendered controls."""

        value = self.initial.get(key, "")
        return str(value or "").strip()

    def apply(self, *, actor: User) -> Loan:
        """Persist the return through the loan manager."""

        loan = self.cleaned_data["loan"]
        if not isinstance(loan, Loan):
            raise TypeError("Expected cleaned loan to be a Loan.")
        return Loan.objects.return_copy(actor=actor, loan=loan)
