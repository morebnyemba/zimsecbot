from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Plan(BaseModel):
    class BillingPeriod(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        TERM = "term", "Term"
        ANNUAL = "annual", "Annual"

    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billing_period = models.CharField(
        max_length=20, choices=BillingPeriod.choices, default=BillingPeriod.MONTHLY
    )
    features = models.JSONField(default=list, blank=True)
    quotas = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price"]

    def __str__(self):
        return self.name


class Subscription(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past Due"
        GRACE = "grace", "Grace Period"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        null=True,
        blank=True,
    )
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="subscriptions",
        null=True,
        blank=True,
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)

    class Meta:
        ordering = ["-current_period_end"]

    def __str__(self):
        owner = self.user_id or self.school_id
        return f"Subscription<{owner}:{self.plan.code}>"


class Payment(BaseModel):
    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        FAILED = "failed", "Failed"

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    provider = models.CharField(max_length=30, default="paynow")
    provider_reference = models.CharField(max_length=255, blank=True, default="")
    poll_url = models.URLField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["provider_reference"])]

    def __str__(self):
        return f"Payment<{self.provider_reference or self.id}:{self.status}>"


class UsageRecord(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usage_records"
    )
    feature_key = models.CharField(max_length=50)
    count = models.PositiveIntegerField(default=0)
    period_date = models.DateField()

    class Meta:
        ordering = ["-period_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "feature_key", "period_date"],
                name="unique_usage_per_user_feature_day",
            )
        ]

    def __str__(self):
        return f"UsageRecord<{self.user_id}:{self.feature_key}:{self.period_date}>"
