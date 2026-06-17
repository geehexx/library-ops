"""Forms for the catalog presentation slice."""

from __future__ import annotations

from django import forms

from libraryops.catalog.models import CatalogFoundationData, ContributorRole


class CatalogFoundationCreateForm(forms.Form):
    """Collect the related fields needed for one foundation record."""

    title = forms.CharField(max_length=255, label="Work title")
    contributor_name = forms.CharField(max_length=255, label="Contributor name")
    contributor_role = forms.ChoiceField(
        choices=ContributorRole.choices,
        initial=ContributorRole.AUTHOR,
        label="Contributor role",
    )
    isbn = forms.CharField(max_length=32, label="ISBN")
    barcode = forms.CharField(max_length=64, label="Barcode")
    publisher = forms.CharField(max_length=255, required=False, label="Publisher")
    publication_year = forms.IntegerField(required=False, min_value=0, label="Publication year")
    language = forms.CharField(max_length=16, initial="en", label="Language")
    shelf_location = forms.CharField(max_length=64, required=False, label="Shelf location")

    def to_payload(self) -> CatalogFoundationData:
        """Convert cleaned form data into a service payload."""

        data = self.cleaned_data
        return CatalogFoundationData(
            title=str(data["title"]),
            contributor_name=str(data["contributor_name"]),
            contributor_role=str(data["contributor_role"]),
            isbn=str(data["isbn"]),
            barcode=str(data["barcode"]),
            publisher=str(data["publisher"]),
            publication_year=data["publication_year"],
            language=str(data["language"]),
            shelf_location=str(data["shelf_location"]),
        )
