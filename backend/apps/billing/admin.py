from django.contrib import admin

from .models import Payment, Plan, Subscription, UsageRecord


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "price", "billing_period", "is_active")
    list_filter = ("billing_period", "is_active")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "school", "plan", "status", "current_period_end", "auto_renew")
    list_filter = ("status", "plan")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("subscription", "amount", "provider", "status", "created_at")
    list_filter = ("provider", "status")


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "feature_key", "count", "period_date")
    list_filter = ("feature_key",)
