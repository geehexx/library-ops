# pyright: reportMissingTypeArgument=false, reportUnknownMemberType=false
"""Edition form for catalog create and update flows."""

from __future__ import annotations

from typing import Any, cast

from django import forms
from django.contrib.auth.models import User

from libraryops.catalog import selectors
from libraryops.catalog.models import BibliographicWork, BookEdition


class EditionForm(forms.ModelForm):
    """Collect edition metadata for create and update flows."""

    work = forms.ModelChoiceField(queryset=selectors.work_list(), label="Work")

    class Meta:
        """Bind the form to the catalog edition model."""

        model = BookEdition
        fields = (
            "work",
            "publisher",
            "publication_year",
            "language",
            "isbn",
            "description",
            "external_identifiers",
        )
        labels = {
            "work": "Work",
            "publisher": "Publisher",
            "publication_year": "Publication year",
            "language": "Language",
            "isbn": "ISBN",
            "description": "Description",
            "external_identifiers": "External identifiers (JSON)",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "external_identifiers": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Refresh relation querysets when rendering or binding the form."""

        super().__init__(*args, **kwargs)
        work_field = cast(Any, self.fields["work"])
        work_field.queryset = selectors.work_list()

    def apply(self, *, actor: User) -> BookEdition:
        """Persist the edition through the owning manager."""

        work = cast(BibliographicWork, self.cleaned_data["work"])
        publisher = str(self.cleaned_data["publisher"])
        publication_year = self.cleaned_data["publication_year"]
        language = str(self.cleaned_data["language"])
        isbn = self.cleaned_data["isbn"] or None
        description = str(self.cleaned_data["description"])
        external_identifiers = cast(
            dict[str, Any],
            self.cleaned_data["external_identifiers"] or {},
        )
        edition = cast(BookEdition, cast(Any, self.instance))
        if edition.pk:
            persisted_edition = BookEdition.objects.get(pk=edition.pk)
            return BookEdition.objects.update_edition(
                actor=actor,
                edition=persisted_edition,
                work=work,
                publisher=publisher,
                publication_year=publication_year,
                language=language,
                isbn=isbn,
                description=description,
                external_identifiers=external_identifiers,
            )
        return BookEdition.objects.create_edition(
            actor=actor,
            work=work,
            publisher=publisher,
            publication_year=publication_year,
            language=language,
            isbn=isbn,
            description=description,
            external_identifiers=external_identifiers,
        )

    def archive(self, *, actor: User) -> BookEdition:
        """Archive the bound edition through the owning manager."""

        edition = cast(BookEdition, cast(Any, self.instance))
        if not edition.pk:
            raise ValueError("Cannot archive an unsaved edition.")
        persisted_edition = BookEdition.objects.get(pk=edition.pk)
        return BookEdition.objects.archive_edition(actor=actor, edition=persisted_edition)
