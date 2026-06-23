import hashlib
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Payment, Plan, Subscription, UsageRecord
from .providers import PaynowProvider
from .services import AccessDenied, AccessGate, get_active_plan, get_free_plan

User = get_user_model()


@pytest.fixture
def student(db):
    return User.objects.create_user(email="student@example.com", password="testpass123")


@pytest.mark.django_db
def test_free_plan_is_auto_created_and_used_by_default(student):
    plan = get_active_plan(student)
    assert plan.code == "free"


@pytest.mark.django_db
def test_active_subscription_overrides_free_plan(student):
    plus = Plan.objects.create(name="Plus", code="plus_test", price=2, features=["ai_tutor"])
    now = timezone.now()
    Subscription.objects.create(
        user=student,
        plan=plus,
        status=Subscription.Status.ACTIVE,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )

    plan = get_active_plan(student)
    assert plan.code == "plus_test"


@pytest.mark.django_db
def test_access_gate_denies_feature_not_on_plan(student):
    get_free_plan()
    with pytest.raises(AccessDenied):
        AccessGate.check(student, "teacher_dashboard")


@pytest.mark.django_db
def test_access_gate_denies_when_quota_exhausted(student):
    plan = get_free_plan()
    plan.quotas = {"ai_tutor": 2}
    plan.features = ["ai_tutor"]
    plan.save()
    UsageRecord.objects.create(
        user=student, feature_key="ai_tutor", count=2, period_date=timezone.localdate()
    )

    with pytest.raises(AccessDenied):
        AccessGate.check(student, "ai_tutor")


@pytest.mark.django_db
def test_access_gate_allows_under_quota(student):
    plan = get_free_plan()
    plan.quotas = {"ai_tutor": 5}
    plan.features = ["ai_tutor"]
    plan.save()

    assert AccessGate.check(student, "ai_tutor") is True


@pytest.mark.django_db
def test_record_usage_increments_existing_record(student):
    AccessGate.record_usage(student, "ai_tutor")
    AccessGate.record_usage(student, "ai_tutor")

    record = UsageRecord.objects.get(user=student, feature_key="ai_tutor")
    assert record.count == 2


@pytest.mark.django_db
def test_plan_list_view_is_public(db):
    Plan.objects.create(name="Plus", code="plus_public_test", price=2, is_active=True)
    client = APIClient()

    response = client.get("/api/v1/billing/plans/")

    assert response.status_code == 200
    results = response.data.get("results", response.data)
    assert any(p["code"] == "plus_public_test" for p in results)


@pytest.mark.django_db
def test_ai_tutor_ask_denied_when_quota_exhausted(student):
    plan = get_free_plan()
    plan.quotas = {"ai_tutor": 1}
    plan.features = ["ai_tutor"]
    plan.save()
    UsageRecord.objects.create(
        user=student, feature_key="ai_tutor", count=1, period_date=timezone.localdate()
    )

    client = APIClient()
    client.force_authenticate(user=student)
    response = client.post("/api/v1/ai-tutor/ask/", {"question": "What is gravity?"})

    assert response.status_code == 403
    assert response.data["error"]["code"] == "feature_locked"


def test_paynow_provider_verifies_valid_hash():
    provider = PaynowProvider.__new__(PaynowProvider)
    with patch("apps.billing.providers.settings") as mock_settings:
        mock_settings.PAYNOW_INTEGRATION_KEY = "mykey"
        data = {"reference": "ref1", "status": "Paid", "amount": "5.00"}
        out = "".join(str(v) for v in data.values()) + "mykey".lower()
        data["hash"] = hashlib.sha512(out.encode("utf-8")).hexdigest().upper()

        assert provider.verify_webhook_hash(data) is True


def test_paynow_provider_rejects_invalid_hash():
    provider = PaynowProvider.__new__(PaynowProvider)
    with patch("apps.billing.providers.settings") as mock_settings:
        mock_settings.PAYNOW_INTEGRATION_KEY = "mykey"
        data = {"reference": "ref1", "status": "Paid", "amount": "5.00", "hash": "bogus"}

        assert provider.verify_webhook_hash(data) is False


@pytest.mark.django_db
@patch("apps.billing.views.PaynowProvider")
def test_webhook_activates_subscription_on_paid_status(mock_provider_cls, student):
    plan = Plan.objects.create(name="Plus", code="plus2", price=2)
    now = timezone.now()
    subscription = Subscription.objects.create(
        user=student,
        plan=plan,
        status=Subscription.Status.PAST_DUE,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )
    payment = Payment.objects.create(
        subscription=subscription, amount=2, provider_reference="ref-123"
    )

    mock_provider = MagicMock()
    mock_provider.verify_webhook_hash.return_value = True
    mock_provider_cls.return_value = mock_provider

    client = APIClient()
    response = client.post(
        "/api/v1/billing/webhook/paynow/",
        {"reference": "ref-123", "status": "Paid", "hash": "anything"},
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    subscription.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert subscription.status == Subscription.Status.ACTIVE


@pytest.mark.django_db
@patch("apps.billing.views.PaynowProvider")
def test_webhook_rejects_invalid_hash(mock_provider_cls, student):
    plan = Plan.objects.create(name="Plus", code="plus3", price=2)
    now = timezone.now()
    subscription = Subscription.objects.create(
        user=student,
        plan=plan,
        status=Subscription.Status.PAST_DUE,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )
    Payment.objects.create(subscription=subscription, amount=2, provider_reference="ref-456")

    mock_provider = MagicMock()
    mock_provider.verify_webhook_hash.return_value = False
    mock_provider_cls.return_value = mock_provider

    client = APIClient()
    response = client.post(
        "/api/v1/billing/webhook/paynow/",
        {"reference": "ref-456", "status": "Paid", "hash": "bogus"},
    )

    assert response.status_code == 403
