"""Role-aware permission mixins for the Django UI layer."""

from __future__ import annotations

from typing import Any, cast

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.views import redirect_to_login
from django.views.generic.base import ContextMixin

from libraryops.accounts.roles import CATALOG_CREATE_PERMISSIONS, resolve_role_name

AppUser = User | AnonymousUser


def get_user_role(user: AppUser) -> str | None:
    """Return the highest-priority application role for a user."""

    if not user.is_authenticated:
        return None
    user_any = cast("Any", user)
    return resolve_role_name(set(user_any.groups.values_list("name", flat=True)))


class RoleContextMixin(ContextMixin):
    """Expose role-aware navigation flags to Django templates."""

    request: Any

    def get_user_role(self) -> str | None:
        """Return the current request user's application role."""

        return get_user_role(self.request.user)

    def can_manage_catalog(self) -> bool:
        """Return whether the current request user may mutate catalog data."""

        user = self.request.user
        return bool(user.is_authenticated and user.has_perms(CATALOG_CREATE_PERMISSIONS))

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Attach role-aware template flags to the standard context."""

        context = super().get_context_data(**kwargs)
        context.setdefault("role", self.get_user_role())
        context.setdefault("can_manage_catalog", self.can_manage_catalog())
        return context


class CatalogManagerRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin, RoleContextMixin):
    """Require the Phase 1 catalog-management permission bundle."""

    permission_required = CATALOG_CREATE_PERMISSIONS
    raise_exception = True

    def handle_no_permission(self):
        """Redirect anonymous users but raise for authenticated permission failures."""

        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        return PermissionRequiredMixin.handle_no_permission(self)
