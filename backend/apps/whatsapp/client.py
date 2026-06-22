import requests
from django.conf import settings

GRAPH_API_VERSION = "v20.0"


class WhatsAppClient:
    """Thin wrapper around the Meta WhatsApp Cloud API send endpoint."""

    def __init__(self, access_token=None, phone_number_id=None):
        self.access_token = access_token or settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
        self.base_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{self.phone_number_id}"

    def _post(self, payload):
        response = requests.post(
            f"{self.base_url}/messages",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def send_text(self, to, body):
        return self._post(
            {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body},
            }
        )

    def send_buttons(self, to, body, buttons):
        """buttons: list of {"id": str, "title": str}, max 3 (Meta limit)."""
        return self._post(
            {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": body},
                    "action": {
                        "buttons": [
                            {"type": "reply", "reply": {"id": b["id"], "title": b["title"][:20]}}
                            for b in buttons[:3]
                        ]
                    },
                },
            }
        )

    def send_list(self, to, body, button_text, rows, section_title="Options"):
        """rows: list of {"id": str, "title": str, "description": str}, max 10 (Meta limit)."""
        return self._post(
            {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "body": {"text": body},
                    "action": {
                        "button": button_text[:20],
                        "sections": [
                            {
                                "title": section_title[:24],
                                "rows": [
                                    {
                                        "id": row["id"],
                                        "title": row["title"][:24],
                                        "description": row.get("description", "")[:72],
                                    }
                                    for row in rows[:10]
                                ],
                            }
                        ],
                    },
                },
            }
        )

    def send_document(self, to, link, filename=None, caption=None):
        document = {"link": link}
        if filename:
            document["filename"] = filename
        if caption:
            document["caption"] = caption
        return self._post(
            {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "document",
                "document": document,
            }
        )

    def send_image(self, to, link, caption=None):
        image = {"link": link}
        if caption:
            image["caption"] = caption
        return self._post(
            {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "image",
                "image": image,
            }
        )

    def mark_as_read(self, message_id):
        return self._post(
            {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
            }
        )
