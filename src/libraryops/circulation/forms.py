"""Circulation workflow forms for checkout and return actions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, cast

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.html import format_html, format_html_join

from libraryops.accounts.roles import ROLE_MEMBER
from libraryops.catalog import selectors
from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopy, BookCopyStatus

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.db.models import QuerySet
    from django.utils.safestring import SafeString


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
    ) -> SafeString:
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
        queryset: QuerySet[Any],
        option_label: Callable[[Any], str],
        resolver: Callable[[str, QuerySet[Any]], Any | None],
        datalist_id: str,
        **kwargs: Any,
    ) -> None:
        self.queryset = queryset
        self._option_label = option_label
        self._resolver = resolver
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


def _normalized_choice(value: str) -> str:
    """Normalize one typed choice for comparison."""

    return " ".join(value.strip().split()).casefold()


def _borrower_display_name(user: User) -> str:
    """Return a human-facing borrower name from durable user data."""

    full_name = user.get_full_name().strip()
    if full_name:
        return full_name
    username = user.get_username().strip()
    local_part = username.split("@", 1)[0]
    local_part = local_part.replace(".", " ").replace("_", " ").replace("-", " ")
    fallback = " ".join(local_part.split()).title()
    return fallback or f"Borrower {user.pk or ''}".strip()


def _borrower_identifier(user: User) -> str:
    """Return the library-style borrower identifier."""

    if user.pk is None:
        return "PATRON-UNSAVED"
    return f"PATRON-{user.pk:04d}"


def _borrower_label(user: User) -> str:
    """Return the autocomplete label for one borrower."""

    return f"{_borrower_display_name(user)} ({_borrower_identifier(user)})"


def _copy_label(copy: BookCopy) -> str:
    """Return the autocomplete label for one copy."""

    edition = cast("Any", copy.edition)
    return f"{copy.barcode} · {edition.work.title}"


def _loan_label(loan: Loan) -> str:
    """Return the autocomplete label for one loan."""

    copy: BookCopy = cast("BookCopy", loan.copy)
    borrower: User = cast("User", loan.borrower)
    return f"{_copy_label(copy)} · {_borrower_label(borrower)}"


def _loan_aliases(loan: Loan) -> tuple[str, ...]:
    """Return the searchable labels for one loan."""

    copy: BookCopy = cast("BookCopy", loan.copy)
    borrower: User = cast("User", loan.borrower)
    return (
        _loan_label(loan),
        _copy_label(copy),
        copy.barcode,
        _borrower_label(borrower),
        _borrower_display_name(borrower),
        _borrower_identifier(borrower),
        str(loan.pk) if loan.pk is not None else "",
    )


def _match_choice(
    value: str,
    queryset: QuerySet[Any],
    aliases: Callable[[Any], tuple[str, ...]],
) -> Any | None:
    """Return the unique queryset instance matching one typed value."""

    normalized_value = _normalized_choice(value)
    if not normalized_value:
        return None
    candidates = list(queryset)
    if normalized_value.isdigit():
        for instance in candidates:
            if instance.pk is not None and str(instance.pk) == normalized_value:
                return instance
    exact_matches = [
        instance
        for instance in candidates
        if normalized_value in {_normalized_choice(alias) for alias in aliases(instance)}
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if exact_matches:
        return None
    partial_matches = [
        instance
        for instance in candidates
        if any(normalized_value in _normalized_choice(alias) for alias in aliases(instance))
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    return None


def _resolve_copy(value: str, queryset: QuerySet[BookCopy]) -> BookCopy | None:
    """Resolve one selected copy from its display label or barcode."""

    return cast(
        "BookCopy | None",
        _match_choice(
            value,
            queryset,
            lambda copy: (
                _copy_label(copy),
                copy.barcode,
                copy.edition.work.title,
                str(copy.pk) if copy.pk is not None else "",
            ),
        ),
    )


def _resolve_borrower(value: str, queryset: QuerySet[User]) -> User | None:
    """Resolve one selected borrower from a human name or patron code."""

    return cast(
        "User | None",
        _match_choice(
            value,
            queryset,
            lambda user: (
                _borrower_label(user),
                _borrower_display_name(user),
                _borrower_identifier(user),
                user.email,
                user.username,
            ),
        ),
    )


def _resolve_loan(value: str, queryset: QuerySet[Loan]) -> Loan | None:
    """Resolve one selected loan from its copy or borrower label."""

    return cast(
        "Loan | None",
        _match_choice(
            value,
            queryset,
            _loan_aliases,
        ),
    )


class CheckoutForm(forms.Form):
    """Collect the data needed to checkout one available copy."""

    copy = AutocompleteLookupField(
        queryset=BookCopy.objects.none(),
        option_label=_copy_label,
        resolver=_resolve_copy,
        datalist_id="checkout-copy-options",
        label="Copy",
        help_text="Start typing a barcode or title, then choose an available copy.",
    )
    borrower = AutocompleteLookupField(
        queryset=User.objects.none(),
        option_label=_borrower_label,
        resolver=_resolve_borrower,
        datalist_id="checkout-borrower-options",
        label="Borrower",
        help_text="Start typing a member name or patron code, then choose a borrower.",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Refresh the dynamic querysets used by the workflow."""

        super().__init__(*args, **kwargs)
        copy_queryset = (
            selectors.copy_list()
            .filter(status=BookCopyStatus.AVAILABLE)
            .order_by(
                "edition__work__title",
                "barcode",
            )
        )
        borrower_queryset = (
            User.objects.filter(groups__name=ROLE_MEMBER).order_by("email").distinct()
        )
        copy_field = cast("AutocompleteLookupField", self.fields["copy"])
        copy_field.set_queryset(copy_queryset)
        copy_field.widget.attrs["autofocus"] = "autofocus"
        borrower_field = cast("AutocompleteLookupField", self.fields["borrower"])
        borrower_field.set_queryset(borrower_queryset)

    def apply(self, *, actor: User) -> Loan:
        """Persist the checkout through the loan manager."""

        copy = cast("BookCopy", self.cleaned_data["copy"])
        borrower = cast("User", self.cleaned_data["borrower"])
        return Loan.objects.checkout_copy(actor=actor, copy=copy, borrower=borrower)


class ReturnForm(forms.Form):
    """Collect the data needed to return one active loan."""

    loan = AutocompleteLookupField(
        queryset=Loan.objects.none(),
        option_label=_loan_label,
        resolver=_resolve_loan,
        datalist_id="return-loan-options",
        label="Loan",
        help_text="Start typing a copy barcode or borrower name, then choose an active loan.",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Refresh the dynamic loan queryset used by the workflow."""

        super().__init__(*args, **kwargs)
        loan_queryset = (
            Loan.objects.select_related("copy__edition__work", "borrower")
            .filter(returned_at__isnull=True)
            .order_by("due_at", "-checked_out_at")
        )
        loan_field = cast("AutocompleteLookupField", self.fields["loan"])
        loan_field.set_queryset(loan_queryset)
        loan_field.widget.attrs["autofocus"] = "autofocus"

    def apply(self, *, actor: User) -> Loan:
        """Persist the return through the loan manager."""

        loan = cast("Loan", self.cleaned_data["loan"])
        return Loan.objects.return_copy(actor=actor, loan=loan)
