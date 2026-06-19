"""Django admin registrations for the catalog app."""

from django.contrib import admin

from .models import (
    BibliographicWork,
    BookEdition,
    Contributor,
    ExternalSourceRecord,
    WorkContributor,
)


@admin.register(BibliographicWork)
class BibliographicWorkAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument]
    """Admin for conceptual works."""

    list_display = (
        "title",
        "normalized_title",
        "archived_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("archived_at",)
    search_fields = ("title", "normalized_title", "description")
    readonly_fields = ("normalized_title", "created_at", "updated_at")
    date_hierarchy = "created_at"


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument]
    """Admin for contributor identities."""

    list_display = ("name", "normalized_name", "created_at")
    search_fields = ("name", "normalized_name")
    readonly_fields = ("normalized_name", "created_at")
    date_hierarchy = "created_at"


@admin.register(WorkContributor)
class WorkContributorAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument]
    """Admin for work-to-contributor assignments."""

    list_display = ("work", "contributor", "role", "sort_order")
    list_filter = ("role",)
    search_fields = ("work__title", "contributor__name")
    autocomplete_fields = ("work", "contributor")
    ordering = ("sort_order", "id")


@admin.register(BookEdition)
class BookEditionAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument]
    """Admin for book editions and publication records."""

    list_display = (
        "work",
        "publisher",
        "publication_year",
        "language",
        "isbn",
        "archived_at",
        "created_at",
    )
    list_filter = ("language", "archived_at")
    search_fields = ("work__title", "publisher", "isbn", "description")
    autocomplete_fields = ("work",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_select_related = ("work",)


@admin.register(ExternalSourceRecord)
class ExternalSourceRecordAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument]
    """Admin for imported provenance records."""

    list_display = (
        "source_name",
        "source_identifier",
        "work",
        "edition",
        "imported_at",
        "fetched_at",
    )
    list_filter = ("source_name",)
    search_fields = (
        "source_name",
        "source_identifier",
        "source_url",
        "license_note",
        "work__title",
        "edition__isbn",
    )
    autocomplete_fields = ("work", "edition")
    readonly_fields = ("imported_at", "fetched_at")
    date_hierarchy = "imported_at"
    list_select_related = ("work", "edition")
