from django.urls import path

from .views import (
    CancelView,
    PaynowWebhookView,
    PlanListView,
    SubscribeView,
    SubscriptionDetailView,
    UsageView,
)

urlpatterns = [
    path("billing/plans/", PlanListView.as_view(), name="billing-plans"),
    path("billing/subscription/", SubscriptionDetailView.as_view(), name="billing-subscription"),
    path("billing/subscribe/", SubscribeView.as_view(), name="billing-subscribe"),
    path("billing/cancel/", CancelView.as_view(), name="billing-cancel"),
    path("billing/usage/", UsageView.as_view(), name="billing-usage"),
    path("billing/webhook/paynow/", PaynowWebhookView.as_view(), name="billing-paynow-webhook"),
]
