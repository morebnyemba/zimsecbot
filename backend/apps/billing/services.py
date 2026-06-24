from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Plan, Subscription, UsageRecord

FREE_PLAN_CODE = "free"
PLAN_CACHE_TTL = 300


class AccessDenied(Exception):
    def __init__(self, message, upgrade_url="/billing/plans/"):
        self.message = message
        self.upgrade_url = upgrade_url
        super().__init__(message)


def get_free_plan():
    plan, _ = Plan.objects.get_or_create(
        code=FREE_PLAN_CODE,
        defaults={
            "name": "Free",
            "price": 0,
            "billing_period": Plan.BillingPeriod.MONTHLY,
            "features": [],
            "quotas": {},
            "is_active": True,
        },
    )
    return plan


def get_active_plan(user):
    cache_key = f"billing:plan:{user.id}"
    plan = cache.get(cache_key)
    if plan is not None:
        return plan

    subscription = (
        Subscription.objects.filter(
            user=user,
            status__in=[Subscription.Status.ACTIVE, Subscription.Status.GRACE],
        )
        .select_related("plan")
        .order_by("-current_period_end")
        .first()
    )
    plan = subscription.plan if subscription else get_free_plan()
    cache.set(cache_key, plan, PLAN_CACHE_TTL)
    return plan


def invalidate_plan_cache(user):
    cache.delete(f"billing:plan:{user.id}")


class AccessGate:
    @staticmethod
    def check(user, feature_key):
        plan = get_active_plan(user)
        if feature_key not in plan.features:
            raise AccessDenied(f"'{feature_key}' requires a plan upgrade.")

        quota = plan.quotas.get(feature_key)
        if quota is not None:
            used = AccessGate._usage_today(user, feature_key)
            if used >= quota:
                raise AccessDenied(
                    f"Daily limit for '{feature_key}' reached ({quota}/day) on your plan."
                )
        return True

    @staticmethod
    def _usage_today(user, feature_key):
        today = timezone.localdate()
        record = UsageRecord.objects.filter(
            user=user, feature_key=feature_key, period_date=today
        ).first()
        return record.count if record else 0

    @staticmethod
    @transaction.atomic
    def record_usage(user, feature_key, amount=1):
        today = timezone.localdate()
        record, created = UsageRecord.objects.get_or_create(
            user=user, feature_key=feature_key, period_date=today, defaults={"count": amount}
        )
        if not created:
            record.count = F("count") + amount
            record.save(update_fields=["count"])
        return record
