"""Circulation URL configuration."""

from __future__ import annotations

from django.urls import path

from libraryops.circulation.views import LoanCheckoutView, LoanDashboardView, LoanReturnView

urlpatterns = [
    path("", LoanDashboardView.as_view(), name="loan-dashboard"),
    path("checkout/", LoanCheckoutView.as_view(), name="loan-checkout"),
    path("return/", LoanReturnView.as_view(), name="loan-return"),
]
