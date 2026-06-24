import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_returns_ok():
    response = APIClient().get("/health/")

    assert response.status_code == 200
    assert response.data == {"status": "ok", "checks": {"database": True, "cache": True}}
