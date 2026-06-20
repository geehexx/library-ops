# pyright: reportMissingTypeArgument=false, reportUnknownMemberType=false
"""Work form for catalog create and update flows."""

from __future__ import annotations

from typing import cast

from django import forms
from django.contrib.auth.models import User

from libraryops.catalog.models import BibliographicWork


class WorkForm(forms.ModelForm):
    """Collect work metadata for create and update flows."""

    class Meta:
        """Bind the form to the catalog work model."""

        model = BibliographicWork
        fields = ("title", "description")
        labels = {"title": "Work title", "description": "Description"}
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def apply(self, *, actor: User) -> BibliographicWork:
        """Persist the work through the owning manager."""

        title = str(self.cleaned_data["title"])
        description = str(self.cleaned_data["description"])
        work = cast(BibliographicWork, self.instance)
        if work.pk:
            persisted_work = BibliographicWork.objects.get(pk=work.pk)
            return BibliographicWork.objects.update_work(
                actor=actor,
                work=persisted_work,
                title=title,
                description=description,
            )
        return BibliographicWork.objects.create_work(
            actor=actor,
            title=title,
            description=description,
        )

    def archive(self, *, actor: User) -> BibliographicWork:
        """Archive the bound work through the owning manager."""

        work = cast(BibliographicWork, self.instance)
        if not work.pk:
            raise ValueError("Cannot archive an unsaved work.")
        persisted_work = BibliographicWork.objects.get(pk=work.pk)
        return BibliographicWork.objects.archive_work(actor=actor, work=persisted_work)
