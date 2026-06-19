"""Circulation workflow forms for checkout and return actions."""

from __future__ import annotations

from typing import Any, cast

from django import forms
from django.contrib.auth.models import User

from libraryops.accounts.roles import ROLE_MEMBER
from libraryops.catalog import selectors
from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopy, BookCopyStatus


class CheckoutForm(forms.Form):
    """Collect the data needed to checkout one available copy."""

    copy = forms.ModelChoiceField(queryset=selectors.copy_list(), label="Copy")
    borrower = forms.ModelChoiceField(queryset=User.objects.none(), label="Borrower")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Refresh the dynamic querysets used by the workflow."""

        super().__init__(*args, **kwargs)
        copy_field = cast(Any, self.fields["copy"])
        copy_field.queryset = selectors.copy_list().filter(status=BookCopyStatus.AVAILABLE)
        borrower_field = cast(Any, self.fields["borrower"])
        borrower_field.queryset = (
            User.objects.filter(groups__name=ROLE_MEMBER).order_by("email").distinct()
        )

    def apply(self, *, actor: User) -> Loan:
        """Persist the checkout through the loan manager."""

        copy = cast(BookCopy, self.cleaned_data["copy"])
        borrower = cast(User, self.cleaned_data["borrower"])
        return Loan.objects.checkout_copy(actor=actor, copy=copy, borrower=borrower)


class ReturnForm(forms.Form):
    """Collect the data needed to return one active loan."""

    loan = forms.ModelChoiceField(queryset=Loan.objects.none(), label="Loan")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Refresh the dynamic loan queryset used by the workflow."""

        super().__init__(*args, **kwargs)
        loan_field = cast(Any, self.fields["loan"])
        loan_field.queryset = (
            Loan.objects.select_related("copy__edition__work", "borrower")
            .filter(returned_at__isnull=True)
            .order_by("due_at", "-checked_out_at")
        )

    def apply(self, *, actor: User) -> Loan:
        """Persist the return through the loan manager."""

        loan = cast(Loan, self.cleaned_data["loan"])
        return Loan.objects.return_copy(actor=actor, loan=loan)
