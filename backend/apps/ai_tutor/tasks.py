import logging

from celery import shared_task

from apps.whatsapp.client import WhatsAppClient

from .models import AISession
from .services import ask

logger = logging.getLogger(__name__)


@shared_task
def answer_whatsapp_question(phone_number: str, question: str):
    session, _ = AISession.objects.get_or_create(
        phone_number=phone_number,
        channel=AISession.Channel.WHATSAPP,
        defaults={"phone_number": phone_number, "channel": AISession.Channel.WHATSAPP},
    )

    try:
        result = ask(session, question)
        answer = result["answer"]
    except Exception:
        logger.exception("AI tutor failed to answer WhatsApp question for %s", phone_number)
        answer = "Sorry, I couldn't process your question right now. Please try again shortly."

    WhatsAppClient().send_text(phone_number, answer)
