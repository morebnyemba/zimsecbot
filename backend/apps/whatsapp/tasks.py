import logging

from celery import shared_task
from django.db import transaction
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

    # Both get_or_create calls below use select_for_update() inside one
    # transaction, closing two race windows the previous plain get_or_create
    # + later save() left open:
    #
    # 1. Meta redelivers the same message_id concurrently (a documented
    #    WhatsApp Cloud API retry behaviour). The old code read
    #    `log.processed_at` *outside* any lock, so a second delivery could
    #    see `created=False, processed_at=None` (the first delivery hadn't
    #    finished yet) and process the same message a second time —
    #    duplicate outbound replies, and for the billing flow, a duplicate
    #    payment-prompt dispatch.
    # 2. The same user sends two messages in quick succession (e.g. a
    #    double-tap on a button). Both tasks read the same ConversationState
    #    row, advance it independently in memory from the same starting
    #    point, and `state.save()` — the second save silently overwrote the
    #    first transition (a lost update), desyncing what the user sees from
    #    `current_step`/`context`.
    #
    # select_for_update() on message_id/phone_number serializes exactly the
    # two cases that must never run concurrently, without holding a lock
    # across unrelated phone numbers or unrelated messages.
    with transaction.atomic():
        log, created = WebhookEventLog.objects.select_for_update().get_or_create(
            message_id=message_id,
            defaults={"phone_number": phone_number, "payload": message},
        )
        if not created and log.processed_at:
            return  # duplicate delivery, already handled

        text, reply_id = _extract_input(message)

        try:
            state, _ = ConversationState.objects.select_for_update().get_or_create(
                phone_number=phone_number
            )
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
