import hashlib

from django.conf import settings
from paynow import Paynow


class PaynowProvider:
    """Thin wrapper around the `paynow` SDK for mobile money push payments.

    The SDK's own `process_status_update` is an unfinished stub (it prints
    "Not implemented" and never sets `status`/`paid`), so webhook payloads
    are verified and parsed manually here using the same hashing scheme the
    SDK uses internally for outbound requests.
    """

    def __init__(self):
        self._client = Paynow(
            settings.PAYNOW_INTEGRATION_ID,
            settings.PAYNOW_INTEGRATION_KEY,
            return_url=f"{settings.PUBLIC_BASE_URL}/billing/return/",
            result_url=f"{settings.PUBLIC_BASE_URL}/api/v1/billing/webhook/paynow/",
        )

    def initiate_mobile_payment(self, *, reference, email, amount, phone, method, item_name):
        payment = self._client.create_payment(reference, email)
        payment.add(item_name, float(amount))
        return self._client.send_mobile(payment, phone, method)

    def verify_webhook_hash(self, data: dict) -> bool:
        provided_hash = data.get("hash", "")
        if not provided_hash:
            return False
        out = "".join(
            str(value) for key, value in data.items() if key.lower() != "hash"
        )
        out += settings.PAYNOW_INTEGRATION_KEY.lower()
        expected = hashlib.sha512(out.encode("utf-8")).hexdigest().upper()
        return expected == provided_hash.upper()
