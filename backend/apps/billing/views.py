import logging
import uuid
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, Plan, Subscription, UsageRecord
from .providers import PaynowProvider
from .serializers import (
    PlanSerializer,
    SubscribeSerializer,
    SubscriptionSerializer,
    UsageRecordSerializer,
)
from .services import invalidate_plan_cache

logger = logging.getLogger(__name__)

PERIOD_DURATIONS = {
    Plan.BillingPeriod.MONTHLY: timedelta(days=30),
    Plan.BillingPeriod.TERM: timedelta(days=120),
    Plan.BillingPeriod.ANNUAL: timedelta(days=365),
}


class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


class SubscriptionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscription = (
            Subscription.objects.filter(
                user=request.user,
                status__in=[Subscription.Status.ACTIVE, Subscription.Status.GRACE],
            )
            .select_related("plan")
            .order_by("-current_period_end")
            .first()
        )
        if not subscription:
            return Response(None)
        return Response(SubscriptionSerializer(subscription).data)


class SubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        plan = get_object_or_404(Plan, code=data["plan_code"], is_active=True)
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status=Subscription.Status.PAST_DUE,
            current_period_start=now,
            current_period_end=now + PERIOD_DURATIONS[plan.billing_period],
            auto_renew=True,
        )
        reference = f"sub-{subscription.id}-{uuid.uuid4().hex[:8]}"
        payment = Payment.objects.create(
            subscription=subscription,
            amount=plan.price,
            provider_reference=reference,
            status=Payment.Status.INITIATED,
        )

        try:
            provider = PaynowProvider()
            result = provider.initiate_mobile_payment(
                reference=reference,
                email=request.user.email,
                amount=plan.price,
                phone=data["phone"],
                method=data["method"],
                item_name=f"{plan.name} subscription",
            )
        except Exception:
            logger.exception("Paynow initiation failed for subscription %s", subscription.id)
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])
            return Response(
                {
                    "error": {
                        "code": "payment_initiation_failed",
                        "message": "Could not start payment.",
                    }
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if not result.success:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])
            error_message = getattr(result, "error", "Payment was rejected.")
            return Response(
                {"error": {"code": "payment_initiation_failed", "message": error_message}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.poll_url = result.poll_url
        payment.save(update_fields=["poll_url"])

        return Response(
            {
                "payment_id": payment.id,
                "subscription_id": subscription.id,
                "instructions": getattr(result, "instruction", ""),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class CancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        subscription = (
            Subscription.objects.filter(
                user=request.user,
                status__in=[Subscription.Status.ACTIVE, Subscription.Status.GRACE],
            )
            .order_by("-current_period_end")
            .first()
        )
        if subscription:
            subscription.auto_renew = False
            subscription.status = Subscription.Status.CANCELLED
            subscription.save(update_fields=["auto_renew", "status"])
            invalidate_plan_cache(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UsageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        records = UsageRecord.objects.filter(user=request.user, period_date=today)
        return Response(UsageRecordSerializer(records, many=True).data)


class PaynowWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        reference = data.get("reference")
        if not reference:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.select_related("subscription").filter(
            provider_reference=reference
        ).first()
        if not payment:
            return Response(status=status.HTTP_404_NOT_FOUND)

        provider = PaynowProvider()
        if not provider.verify_webhook_hash(data):
            return Response(status=status.HTTP_403_FORBIDDEN)

        paynow_status = str(data.get("status", "")).lower()
        if paynow_status == "paid":
            payment.status = Payment.Status.PAID
            payment.save(update_fields=["status"])
            subscription = payment.subscription
            subscription.status = Subscription.Status.ACTIVE
            subscription.save(update_fields=["status"])
            if subscription.user_id:
                invalidate_plan_cache(subscription.user)
        elif paynow_status == "cancelled":
            payment.status = Payment.Status.CANCELLED
            payment.save(update_fields=["status"])
        else:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])

        return Response(status=status.HTTP_200_OK)
