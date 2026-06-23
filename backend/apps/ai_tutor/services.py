import logging

from apps.knowledge_base.retrieval import search

from .models import AISession, Message
from .providers import get_active_provider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a ZIMSEC STEM tutor helping students revise Maths, Science, and related "
    "subjects. Answer clearly and step by step using only the context provided below. "
    "If the context does not contain enough information to answer confidently, say so "
    "explicitly instead of guessing. Keep answers concise and exam-focused."
)

NO_CONTEXT_DISCLAIMER = (
    "\n\n(Note: I couldn't find this topic in the knowledge base, so this answer is "
    "based on general knowledge and may be incomplete. Please verify with your teacher "
    "or textbook.)"
)


def ask(session: AISession, question: str, subject_id=None, topic_id=None) -> dict:
    Message.objects.create(session=session, role=Message.Role.USER, content=question)

    try:
        chunks = search(question, subject_id=subject_id, topic_id=topic_id)
    except Exception:
        logger.exception("Knowledge base retrieval failed for session %s", session.id)
        chunks = []

    context = "\n\n".join(chunk.text for chunk in chunks)
    sources = [
        {"document_id": str(chunk.document_id), "title": chunk.document.title} for chunk in chunks
    ]

    prompt = f"Context:\n{context}\n\nQuestion: {question}" if context else f"Question: {question}"

    try:
        provider = get_active_provider()
        answer = provider.generate(SYSTEM_PROMPT, prompt)
    except Exception:
        logger.exception("Gemini generation failed for session %s", session.id)
        answer = (
            "Sorry, I couldn't generate an answer right now. Please try again in a "
            "moment."
        )
        sources = []

    if not chunks:
        answer = f"{answer}{NO_CONTEXT_DISCLAIMER}"

    Message.objects.create(
        session=session, role=Message.Role.ASSISTANT, content=answer, sources=sources
    )

    return {"answer": answer, "sources": sources}
