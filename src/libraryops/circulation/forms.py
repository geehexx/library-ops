"""Circulation workflow forms for checkout and return actions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar, cast

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils.html import format_html, format_html_join

from libraryops.circulation.models import Loan
from libraryops.circulation.selectors import (
    borrower_label,
    checkout_borrower_queryset,
    checkout_copy_queryset,
    copy_label,
    loan_label,
    resolve_borrower,
    resolve_copy,
    resolve_loan,
    return_loan_queryset,
)
from libraryops.inventory.models import BookCopy


class _AutocompleteTextInput(forms.TextInput):
    """Render a text input with a paired datalist suggestion surface."""

    def __init__(self, *, datalist_id: str, attrs: dict[str, str] | None = None) -> None:
        attrs = dict(attrs or {})
        attrs.setdefault("autocomplete", "off")
        attrs["list"] = datalist_id
        self.datalist_id = datalist_id
        self.options: list[str] = []
        super().__init__(attrs)

    def render(
        self,
        name: str,
        value: Any,
        attrs: dict[str, Any] | None = None,
        renderer: Any | None = None,
    ) -> Any:
        """Render the input alongside its option list."""

        input_html = super().render(name, value, attrs=attrs, renderer=renderer)
        options_html = format_html_join(
            "",
            '<option value="{}"></option>',
            ((option,) for option in self.options),
        )
        return format_html(
            '{}<datalist id="{}">{}</datalist>',
            input_html,
            self.datalist_id,
            options_html,
        )


class AutocompleteLookupField(forms.Field):
    """Resolve one text choice from a queryset using a searchable label."""

    default_error_messages: ClassVar[Any] = {
        "invalid": "Select a valid choice from the suggestions.",
    }

    def __init__(
        self,
        *,
        queryset: Any,
        option_label: Any,
        resolver: Any,
        datalist_id: str,
        **kwargs: Any,
    ) -> None:
        if not isinstance(queryset, QuerySet):
            raise TypeError("queryset must be a QuerySet.")
        if not isinstance(option_label, Callable):
            raise TypeError("option_label must be callable.")
        if not isinstance(resolver, Callable):
            raise TypeError("resolver must be callable.")
        self.queryset: QuerySet[Any] = queryset
        self._option_label: Callable[[Any], str] = option_label
        self._resolver: Callable[[str, QuerySet[Any]], Any | None] = resolver
        self.widget = _AutocompleteTextInput(datalist_id=datalist_id)
        super().__init__(**kwargs)
        self.refresh_options()

    def refresh_options(self) -> None:
        """Refresh the datalist options from the current queryset."""

        widget = cast("_AutocompleteTextInput", self.widget)
        widget.options = [self._option_label(instance) for instance in self.queryset]

    def set_queryset(self, queryset: QuerySet[Any]) -> None:
        """Replace the backing queryset and refresh the rendered suggestions."""

        self.queryset = queryset
        self.refresh_options()

    def clean(self, value: Any) -> Any:
        """Return the selected model instance instead of the raw text value."""

        normalized_value = super().clean(value)
        if normalized_value in self.empty_values:
            return normalized_value
        resolved = self._resolver(str(normalized_value), self.queryset)
        if resolved is None:
            raise ValidationError(self.error_messages["invalid"], code="invalid")
        return resolved


class CheckoutForm(forms.Form):
    """Collect the data needed to checkout one available copy."""

    copy = AutocompleteLookupField(
        queryset=BookCopy.objects.none(),
        option_label=copy_label,
        resolver=resolve_copy,
        datalist_id="checkout-copy-options",
        label="Copy",
        help_text="Start typing a barcode or title, then choose an available copy.",
    )
    borrower = AutocompleteLookupField(
        queryset=User.objects.none(),
        option_label=borrower_label,
        resolver=resolve_borrower,
        datalist_id="checkout-borrower-options",
        label="Borrower",
        help_text="Start typing a member name or patron code, then choose a borrower.",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Refresh the dynamic querysets used by the workflow."""

        super().__init__(*args, **kwargs)
        copy_field = cast("AutocompleteLookupField", self.fields["copy"])
        copy_field.set_queryset(checkout_copy_queryset())
        copy_field.widget.attrs["autofocus"] = "autofocus"
        borrower_field = cast("AutocompleteLookupField", self.fields["borrower"])
        borrower_field.set_queryset(checkout_borrower_queryset())

    def apply(self, *, actor: User) -> Loan:
        """Persist the checkout through the loan manager."""

        copy = cast("BookCopy", self.cleaned_data["copy"])
        borrower = cast("User", self.cleaned_data["borrower"])
        return Loan.objects.checkout_copy(actor=actor, copy=copy, borrower=borrower)


class ReturnForm(forms.Form):
    """Collect the data needed to return one active loan."""

    loan = AutocompleteLookupField(
        queryset=Loan.objects.none(),
        option_label=loan_label,
        resolver=resolve_loan,
        datalist_id="return-loan-options",
        label="Loan",
        help_text="Start typing a copy barcode or borrower name, then choose an active loan.",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Refresh the dynamic loan queryset used by the workflow."""

        super().__init__(*args, **kwargs)
        loan_field = cast("AutocompleteLookupField", self.fields["loan"])
        loan_field.set_queryset(return_loan_queryset())
        loan_field.widget.attrs["autofocus"] = "autofocus"

    def apply(self, *, actor: User) -> Loan:
        """Persist the return through the loan manager."""

        loan = cast("Loan", self.cleaned_data["loan"])
        return Loan.objects.return_copy(actor=actor, loan=loan)
