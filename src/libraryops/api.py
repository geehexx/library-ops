"""Root Django Ninja API shell for Library Ops."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpRequest, HttpResponse  # noqa: TC002
from ninja import NinjaAPI

from libraryops.catalog.api import copies_router, editions_router, works_router

api = NinjaAPI(title="Library Ops API", version="0.1.0")


@api.exception_handler(PermissionDenied)
def _handle_permission_denied(  # pyright: ignore[reportUnusedFunction]
    request: HttpRequest,
    exc: PermissionDenied,
) -> HttpResponse:
    """Return a JSON 403 for catalog mutation permission failures."""

    return api.create_response(
        request,
        {"detail": str(exc) or "Forbidden"},
        status=403,
    )


@api.exception_handler(DjangoValidationError)
def _handle_django_validation_error(  # pyright: ignore[reportUnusedFunction]
    request: HttpRequest,
    exc: DjangoValidationError,
) -> HttpResponse:
    """Return structured JSON for Django model validation failures."""

    message_dict = getattr(exc, "message_dict", None)
    if message_dict:
        detail = [
            {"loc": ["body", field], "msg": message, "type": "value_error"}
            for field, messages in message_dict.items()
            for message in messages
        ]
    else:
        detail = [
            {"loc": ["body"], "msg": message, "type": "value_error"} for message in exc.messages
        ]
    return api.create_response(request, {"detail": detail}, status=422)


api.add_router("/catalog/works", works_router)
api.add_router("/catalog/editions", editions_router)
api.add_router("/catalog/copies", copies_router)
