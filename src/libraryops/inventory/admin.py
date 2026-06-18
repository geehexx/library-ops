"""Django admin registrations for the inventory app."""

from django.contrib import admin

from .models import BookCopy


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument]
    """Admin for physical book copies."""

    list_display = (
        "barcode",
        "edition",
        "status",
        "shelf_location",
        "archived_at",
        "created_at",
    )
    list_filter = ("status", "archived_at")
    search_fields = (
        "barcode",
        "shelf_location",
        "condition_note",
        "edition__isbn",
        "edition__work__title",
    )
    autocomplete_fields = ("edition",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_select_related = ("edition",)
