import logging

from celery import shared_task
from django.utils import timezone

from apps.conversations.engine import handle_inbound_message
from apps.conversations.models import ConversationState

from .client import WhatsAppClient
from .models import WebhookEventLog

logger = logging.getLogger(__name__)


@shared_task
def process_inbound_event(payload):
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                _process_message(message)


def _process_message(message):
    message_id = message.get("id")
    phone_number = message.get("from", "")
    if not message_id or not phone_number:
        return

    log, created = WebhookEventLog.objects.get_or_create(
        message_id=message_id,
        defaults={"phone_number": phone_number, "payload": message},
    )
    if not created and log.processed_at:
        return  # duplicate delivery, already handled

    text, reply_id = _extract_input(message)

    try:
        state, _ = ConversationState.objects.get_or_create(phone_number=phone_number)
        actions = handle_inbound_message(state, text=text, reply_id=reply_id)
        state.save()

        client = WhatsAppClient()
        client.mark_as_read(message_id)
        for action in actions:
            _dispatch_action(client, phone_number, action)
    except Exception:
        logger.exception("Failed to process inbound WhatsApp message %s", message_id)
        log.error = "failed to process"
        log.save(update_fields=["error"])
        return

    log.processed_at = timezone.now()
    log.save(update_fields=["processed_at"])


def _extract_input(message):
    msg_type = message.get("type")
    if msg_type == "text":
        return message.get("text", {}).get("body", ""), None
    if msg_type == "interactive":
        interactive = message.get("interactive", {})
        if interactive.get("type") == "button_reply":
            return None, interactive["button_reply"]["id"]
        if interactive.get("type") == "list_reply":
            return None, interactive["list_reply"]["id"]
    return "", None


def _dispatch_action(client, to, action):
    kind = action["type"]
    if kind == "text":
        client.send_text(to, action["body"])
    elif kind == "buttons":
        client.send_buttons(to, action["body"], action["buttons"])
    elif kind == "list":
        client.send_list(
            to,
            action["body"],
            action["button_text"],
            action["rows"],
            action.get("section_title", "Options"),
        )
    elif kind == "document":
        client.send_document(to, action["link"], action.get("filename"), action.get("caption"))
    elif kind == "image":
        client.send_image(to, action["link"], action.get("caption"))
    elif kind == "enqueue_ai_tutor":
        from apps.ai_tutor.tasks import answer_whatsapp_question

        answer_whatsapp_question.delay(action["phone_number"], action["question"])
    elif kind == "enqueue_subscribe":
        from apps.billing.tasks import process_whatsapp_subscription

        process_whatsapp_subscription.delay(
            action["phone_number"],
            action["user_id"],
            action["plan_code"],
            action["method"],
            action["pay_phone"],
        )
