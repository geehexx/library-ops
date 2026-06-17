"""Shell URL configuration."""

from __future__ import annotations

from django.urls import path

from libraryops.shell.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]
