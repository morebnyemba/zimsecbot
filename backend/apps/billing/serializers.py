from rest_framework import serializers

from .models import Payment, Plan, Subscription, UsageRecord


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "code",
            "price",
            "billing_period",
            "features",
            "quotas",
            "is_active",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "status",
            "current_period_start",
            "current_period_end",
            "auto_renew",
        ]


class SubscribeSerializer(serializers.Serializer):
    plan_code = serializers.SlugField()
    phone = serializers.CharField(max_length=20)
    method = serializers.ChoiceField(choices=["ecocash", "onemoney"])


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "currency",
            "provider",
            "provider_reference",
            "status",
            "created_at",
        ]


class UsageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageRecord
        fields = ["feature_key", "count", "period_date"]
