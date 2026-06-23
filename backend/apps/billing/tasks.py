import logging
import uuid
from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.whatsapp.client import WhatsAppClient

from .models import Payment, Plan, Subscription
from .providers import PaynowProvider

logger = logging.getLogger(__name__)

User = get_user_model()

PERIOD_DURATIONS = {
    Plan.BillingPeriod.MONTHLY: timedelta(days=30),
    Plan.BillingPeriod.TERM: timedelta(days=120),
    Plan.BillingPeriod.ANNUAL: timedelta(days=365),
}


@shared_task
def process_whatsapp_subscription(phone_number, user_id, plan_code, method, pay_phone):
    client = WhatsAppClient()
    user = User.objects.filter(pk=user_id).first()
    plan = Plan.objects.filter(code=plan_code, is_active=True).first()
    if not user or not plan:
        client.send_text(phone_number, "Sorry, that plan is no longer available.")
        return

    now = timezone.now()
    subscription = Subscription.objects.create(
        user=user,
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
            email=user.email,
            amount=plan.price,
            phone=pay_phone,
            method=method,
            item_name=f"{plan.name} subscription",
        )
    except Exception:
        logger.exception("Paynow initiation failed for WhatsApp subscription %s", subscription.id)
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        client.send_text(
            phone_number, "Sorry, we couldn't start your payment. Please try again later."
        )
        return

    if not result.success:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        client.send_text(phone_number, "Payment could not be started. Please try again later.")
        return

    payment.poll_url = result.poll_url
    payment.save(update_fields=["poll_url"])

    instructions = getattr(result, "instruction", "")
    body = "✅ Check your phone for the payment prompt and approve it to activate your plan."
    if instructions:
        body += f"\n\n{instructions}"
    client.send_text(phone_number, body)
