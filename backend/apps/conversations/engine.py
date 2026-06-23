"""Conversation flow engine for the WhatsApp channel.

Routes inbound WhatsApp input through a DB-backed state machine
(`ConversationState`) and returns a list of outbound "actions" for the
caller (a Celery task) to send via the WhatsApp Cloud API client. No
network calls happen here -- this module is pure routing/business logic
so it can be unit tested without mocking HTTP.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.utils import timezone
from django.utils.crypto import get_random_string

from apps.analytics.models import Recommendation, StudyStreak
from apps.billing.models import Plan
from apps.billing.services import AccessDenied, AccessGate
from apps.notes.models import Note
from apps.papers.models import PastPaper
from apps.questions.models import Question
from apps.quizzes import services as quiz_services
from apps.quizzes.models import Quiz, QuizAnswer, QuizAttempt
from apps.subjects.models import Subject, Topic

from .models import ConversationState

User = get_user_model()

GLOBAL_RESET_COMMANDS = {"menu", "0"}
QUIZ_QUESTION_COUNT = 5

HELP_TEXT = (
    "🤖 *ZIMSEC STEM Assistant*\n\n"
    "Reply with the option shown, or use:\n"
    "• *menu* / *0* — return to the main menu\n"
    "• *help* — show this message"
)

MAIN_MENU_ROWS = [
    {"id": "menu_papers", "title": "1. Past Papers"},
    {"id": "menu_revision", "title": "2. Revision Notes"},
    {"id": "menu_quiz", "title": "3. Practice Quiz"},
    {"id": "menu_ai_tutor", "title": "4. Ask AI Tutor"},
    {"id": "menu_study_plan", "title": "5. Study Plan"},
    {"id": "menu_progress", "title": "6. My Progress"},
]

MAIN_MENU_DESTINATIONS = {
    "menu_papers": (ConversationState.Flow.PAST_PAPER, "choose_level"),
    "menu_revision": (ConversationState.Flow.REVISION, "choose_subject"),
    "menu_quiz": (ConversationState.Flow.QUIZ, "choose_subject"),
    "menu_ai_tutor": (ConversationState.Flow.AI_TUTOR, "ask"),
    "menu_study_plan": (ConversationState.Flow.STUDY_PLAN, "intro"),
    "menu_progress": (ConversationState.Flow.PROGRESS, "show"),
}


def handle_inbound_message(state, *, text, reply_id):
    text = (text or "").strip()
    lowered = text.lower()

    _apply_timeout(state)

    if lowered == "help":
        return [{"type": "text", "body": HELP_TEXT}]

    if state.user is None and state.current_flow != ConversationState.Flow.REGISTRATION:
        state.current_flow = ConversationState.Flow.REGISTRATION
        state.current_step = "ask_name"
        state.context = {}
        return [
            {
                "type": "text",
                "body": "👋 Welcome to the ZIMSEC STEM Assistant! What's your full name?",
            }
        ]

    if (
        lowered in GLOBAL_RESET_COMMANDS
        and state.current_flow != ConversationState.Flow.REGISTRATION
    ):
        return _show_main_menu(state)

    handler = _FLOW_HANDLERS.get(state.current_flow, _show_main_menu)
    return handler(state, text=text, reply_id=reply_id)


def _apply_timeout(state):
    if state.current_flow == ConversationState.Flow.MAIN_MENU:
        return
    timeout = timezone.timedelta(minutes=settings.CONVERSATION_TIMEOUT_MINUTES)
    if timezone.now() - state.updated_at > timeout:
        state.reset_to_main_menu()


def _media_url(file_field):
    if not file_field:
        return ""
    return f"{settings.PUBLIC_BASE_URL.rstrip('/')}{file_field.url}"


# --- Main Menu -------------------------------------------------------------


def _show_main_menu(state, text="", reply_id=None):
    if (
        reply_id in MAIN_MENU_DESTINATIONS
        and state.current_flow == ConversationState.Flow.MAIN_MENU
    ):
        flow, step = MAIN_MENU_DESTINATIONS[reply_id]
        state.current_flow = flow
        state.current_step = step
        state.context = {}
        return _FLOW_HANDLERS[flow](state, text="", reply_id=None)

    state.current_flow = ConversationState.Flow.MAIN_MENU
    state.current_step = ""
    state.context = {}
    return [
        {
            "type": "list",
            "body": "📚 *Main Menu*\nWhat would you like to do?",
            "button_text": "Choose",
            "rows": MAIN_MENU_ROWS,
            "section_title": "Main Menu",
        }
    ]


# --- Registration -----------------------------------------------------------


def _registration_flow(state, *, text, reply_id):
    step = state.current_step
    text = (text or "").strip()

    if step == "ask_email":
        email = text.lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            return [
                {
                    "type": "text",
                    "body": "That doesn't look like a valid email. Please try again.",
                }
            ]
        return _complete_registration(state, email)

    # default / "ask_name"
    if not text:
        return [{"type": "text", "body": "What's your full name?"}]
    state.context["name"] = text
    state.current_step = "ask_email"
    return [
        {
            "type": "text",
            "body": "Thanks! What's your email address? (used to sync with the web portal)",
        }
    ]


def _complete_registration(state, email):
    name_parts = state.context.get("name", "").split(maxsplit=1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    user = User.objects.filter(email=email).first()
    if user is None:
        user = User.objects.create_user(
            email=email,
            password=get_random_string(32),
            first_name=first_name,
            last_name=last_name,
            phone_number=state.phone_number,
        )
    elif not user.phone_number:
        user.phone_number = state.phone_number
        user.save(update_fields=["phone_number"])

    state.user = user
    body = f"✅ Welcome, {user.first_name or user.email}! You're all set."
    return [{"type": "text", "body": body}, *_show_main_menu(state)]


# --- Past Paper flow ---------------------------------------------------------


def _past_paper_flow(state, *, text, reply_id):
    step = state.current_step

    if step == "choose_level":
        if reply_id in ("level_o_level", "level_a_level"):
            level = Subject.Level.O_LEVEL if reply_id == "level_o_level" else Subject.Level.A_LEVEL
            state.context["level"] = level
            state.current_step = "choose_subject"
            return _past_paper_subject_prompt(state)
        return [
            {
                "type": "buttons",
                "body": "📄 *Past Papers*\nWhich level?",
                "buttons": [
                    {"id": "level_o_level", "title": "O-Level"},
                    {"id": "level_a_level", "title": "A-Level"},
                ],
            }
        ]

    if step == "choose_subject":
        subject = None
        if reply_id and reply_id.startswith("subject_"):
            subject = Subject.objects.filter(
                id=reply_id.removeprefix("subject_"), is_active=True
            ).first()
        if subject:
            state.context["subject_id"] = str(subject.id)
            state.current_step = "choose_year"
            return _past_paper_year_prompt(state, subject)
        return _past_paper_subject_prompt(state)

    if step == "choose_year":
        subject = Subject.objects.filter(id=state.context.get("subject_id")).first()
        if not subject:
            state.current_step = "choose_subject"
            return _past_paper_subject_prompt(state)
        if reply_id and reply_id.startswith("year_"):
            return _send_past_papers(state, subject, reply_id.removeprefix("year_"))
        return _past_paper_year_prompt(state, subject)

    if step == "after_send":
        if reply_id == "paper_another":
            state.current_step = "choose_subject"
            return _past_paper_subject_prompt(state)
        return _show_main_menu(state)

    state.current_step = "choose_level"
    return _past_paper_flow(state, text="", reply_id=None)


def _past_paper_subject_prompt(state):
    level = state.context.get("level")
    subjects = list(Subject.objects.filter(is_active=True, level=level).order_by("name")[:10])
    if not subjects:
        return [
            {"type": "text", "body": "No subjects found for that level yet."},
            *_show_main_menu(state),
        ]
    rows = [{"id": f"subject_{s.id}", "title": s.name} for s in subjects]
    return [
        {
            "type": "list",
            "body": "Choose a subject:",
            "button_text": "Choose",
            "rows": rows,
            "section_title": "Subjects",
        }
    ]


def _past_paper_year_prompt(state, subject):
    years = list(
        PastPaper.objects.filter(subject=subject)
        .order_by("-year")
        .values_list("year", flat=True)
        .distinct()[:10]
    )
    if not years:
        return [
            {"type": "text", "body": f"No past papers found for {subject.name} yet."},
            *_show_main_menu(state),
        ]
    rows = [{"id": f"year_{year}", "title": str(year)} for year in years]
    return [
        {
            "type": "list",
            "body": f"Choose a year for {subject.name}:",
            "button_text": "Choose",
            "rows": rows,
            "section_title": "Years",
        }
    ]


def _send_past_papers(state, subject, year):
    papers = PastPaper.objects.filter(subject=subject, year=year).select_related("marking_scheme")
    state.current_step = "after_send"
    if not papers:
        return [{"type": "text", "body": "No papers found for that year."}, *_after_paper_buttons()]

    actions = []
    for paper in papers:
        caption = f"{subject.name} {year} {paper.get_session_display()} Paper {paper.paper_number}"
        actions.append(
            {
                "type": "document",
                "link": _media_url(paper.file),
                "filename": f"{subject.code}_{year}_{paper.session}_P{paper.paper_number}.pdf",
                "caption": caption,
            }
        )
        if paper.marking_scheme:
            actions.append(
                {
                    "type": "document",
                    "link": _media_url(paper.marking_scheme.file),
                    "filename": (
                        f"{subject.code}_{year}_{paper.session}_P{paper.paper_number}_marking_scheme.pdf"
                    ),
                    "caption": "Marking scheme",
                }
            )
    actions.extend(_after_paper_buttons())
    return actions


def _after_paper_buttons():
    return [
        {
            "type": "buttons",
            "body": "Would you like another paper?",
            "buttons": [
                {"id": "paper_another", "title": "Another paper"},
                {"id": "paper_done", "title": "Done"},
            ],
        }
    ]


# --- Revision (notes) flow ---------------------------------------------------


def _revision_flow(state, *, text, reply_id):
    step = state.current_step

    if step == "choose_subject":
        subject = None
        if reply_id and reply_id.startswith("subject_"):
            subject = Subject.objects.filter(id=reply_id.removeprefix("subject_")).first()
        if subject:
            state.context["subject_id"] = str(subject.id)
            state.current_step = "choose_topic"
            return _revision_topic_prompt(subject)
        return _revision_subject_prompt()

    if step == "choose_topic":
        subject = Subject.objects.filter(id=state.context.get("subject_id")).first()
        if not subject:
            state.current_step = "choose_subject"
            return _revision_subject_prompt()
        if reply_id and reply_id.startswith("topic_"):
            topic_id = reply_id.removeprefix("topic_")
            topic = None if topic_id == "none" else Topic.objects.filter(id=topic_id).first()
            return _send_notes(state, subject, topic)
        return _revision_topic_prompt(subject)

    if step == "after_send":
        if reply_id == "revision_another_topic":
            subject = Subject.objects.filter(id=state.context.get("subject_id")).first()
            if subject:
                state.current_step = "choose_topic"
                return _revision_topic_prompt(subject)
        return _show_main_menu(state)

    state.current_step = "choose_subject"
    return _revision_subject_prompt()


def _revision_subject_prompt():
    subject_ids = Note.objects.values_list("subject_id", flat=True).distinct()
    subjects = list(
        Subject.objects.filter(id__in=subject_ids, is_active=True).order_by("name")[:10]
    )
    if not subjects:
        return [{"type": "text", "body": "No revision notes are available yet."}]
    rows = [{"id": f"subject_{s.id}", "title": s.name} for s in subjects]
    return [
        {
            "type": "list",
            "body": "📖 *Revision Notes*\nChoose a subject:",
            "button_text": "Choose",
            "rows": rows,
            "section_title": "Subjects",
        }
    ]


def _revision_topic_prompt(subject):
    topic_ids = [
        tid
        for tid in Note.objects.filter(subject=subject)
        .values_list("topic_id", flat=True)
        .distinct()
        if tid
    ]
    topics = list(Topic.objects.filter(id__in=topic_ids).order_by("name")[:9])
    rows = [{"id": f"topic_{t.id}", "title": t.name} for t in topics]
    if Note.objects.filter(subject=subject, topic__isnull=True).exists():
        rows.append({"id": "topic_none", "title": "General notes"})
    if not rows:
        return [{"type": "text", "body": f"No notes found for {subject.name} yet."}]
    return [
        {
            "type": "list",
            "body": f"Choose a topic for {subject.name}:",
            "button_text": "Choose",
            "rows": rows,
            "section_title": "Topics",
        }
    ]


def _send_notes(state, subject, topic):
    notes = list(Note.objects.filter(subject=subject, topic=topic)[:5])
    state.current_step = "after_send"
    actions = []
    if not notes:
        actions.append({"type": "text", "body": "No notes found for that topic."})
    for note in notes:
        actions.append({"type": "text", "body": f"*{note.title}*\n\n{note.content}"})
        for media_item in note.media or []:
            url = media_item.get("url") if isinstance(media_item, dict) else None
            if url:
                actions.append({"type": "image", "link": url, "caption": note.title})
    actions.append(
        {
            "type": "buttons",
            "body": "Want notes on another topic?",
            "buttons": [
                {"id": "revision_another_topic", "title": "Another topic"},
                {"id": "revision_done", "title": "Done"},
            ],
        }
    )
    return actions


# --- Quiz flow ----------------------------------------------------------------


def _quiz_flow(state, *, text, reply_id):
    step = state.current_step

    if step == "choose_subject":
        subject = None
        if reply_id and reply_id.startswith("subject_"):
            subject = Subject.objects.filter(
                id=reply_id.removeprefix("subject_"), is_active=True
            ).first()
        if subject:
            state.context["subject_id"] = str(subject.id)
            state.current_step = "choose_topic"
            return _quiz_topic_prompt(subject)
        return _quiz_subject_prompt()

    if step == "choose_topic":
        subject = Subject.objects.filter(id=state.context.get("subject_id")).first()
        if not subject:
            state.current_step = "choose_subject"
            return _quiz_subject_prompt()
        if reply_id and reply_id.startswith("topic_"):
            topic_id = reply_id.removeprefix("topic_")
            state.context["topic_id"] = None if topic_id == "none" else topic_id
            state.current_step = "choose_difficulty"
            return _quiz_difficulty_prompt()
        return _quiz_topic_prompt(subject)

    if step == "choose_difficulty":
        if reply_id in ("difficulty_easy", "difficulty_medium", "difficulty_hard"):
            return _start_quiz(state, reply_id.removeprefix("difficulty_"))
        return _quiz_difficulty_prompt()

    if step == "question":
        return _handle_quiz_answer(state, reply_id, text)

    state.current_step = "choose_subject"
    return _quiz_subject_prompt()


def _quiz_subject_prompt():
    subjects = list(Subject.objects.filter(is_active=True).order_by("name")[:10])
    rows = [{"id": f"subject_{s.id}", "title": s.name} for s in subjects]
    return [
        {
            "type": "list",
            "body": "📝 *Practice Quiz*\nChoose a subject:",
            "button_text": "Choose",
            "rows": rows,
            "section_title": "Subjects",
        }
    ]


def _quiz_topic_prompt(subject):
    topics = list(Topic.objects.filter(subject=subject).order_by("name")[:9])
    rows = [{"id": "topic_none", "title": "Whole subject"}]
    rows += [{"id": f"topic_{t.id}", "title": t.name} for t in topics]
    return [
        {
            "type": "list",
            "body": f"Choose a topic for {subject.name}:",
            "button_text": "Choose",
            "rows": rows,
            "section_title": "Topics",
        }
    ]


def _quiz_difficulty_prompt():
    return [
        {
            "type": "buttons",
            "body": "Choose a difficulty:",
            "buttons": [
                {"id": "difficulty_easy", "title": "Easy"},
                {"id": "difficulty_medium", "title": "Medium"},
                {"id": "difficulty_hard", "title": "Hard"},
            ],
        }
    ]


def _start_quiz(state, difficulty):
    quiz = quiz_services.generate_quiz(
        user=state.user,
        subject_id=state.context.get("subject_id"),
        topic_id=state.context.get("topic_id"),
        difficulty=difficulty,
        question_count=QUIZ_QUESTION_COUNT,
    )
    question_ids = list(quiz.quiz_questions.order_by("order").values_list("question_id", flat=True))
    if not question_ids:
        return [
            {"type": "text", "body": "No questions available for that selection yet."},
            *_show_main_menu(state),
        ]

    state.context.update(
        {
            "quiz_id": str(quiz.id),
            "question_ids": [str(q) for q in question_ids],
            "index": 0,
            "answers": [],
        }
    )
    state.current_step = "question"
    return _send_quiz_question(state)


def _send_quiz_question(state):
    question_ids = state.context["question_ids"]
    index = state.context["index"]
    question = Question.objects.get(id=question_ids[index])
    body = f"Question {index + 1}/{len(question_ids)}:\n\n{question.question_text}"

    options = question.options or []
    if question.question_type == Question.QuestionType.MCQ and options:
        if len(options) <= 3:
            return [
                {
                    "type": "buttons",
                    "body": body,
                    "buttons": [
                        {"id": f"answer_{i}", "title": opt} for i, opt in enumerate(options)
                    ],
                }
            ]
        if len(options) <= 10:
            return [
                {
                    "type": "list",
                    "body": body,
                    "button_text": "Answer",
                    "rows": [{"id": f"answer_{i}", "title": opt} for i, opt in enumerate(options)],
                    "section_title": "Options",
                }
            ]
        numbered = "\n".join(f"{i + 1}. {opt}" for i, opt in enumerate(options))
        return [{"type": "text", "body": f"{body}\n\n{numbered}\n\nReply with the option number."}]

    return [{"type": "text", "body": f"{body}\n\n(Reply with your answer)"}]


def _resolve_quiz_answer(question, reply_id, text):
    options = question.options or []
    if reply_id and reply_id.startswith("answer_"):
        index = int(reply_id.removeprefix("answer_"))
        if 0 <= index < len(options):
            return options[index]
    stripped = (text or "").strip()
    if stripped.isdigit() and options:
        index = int(stripped) - 1
        if 0 <= index < len(options):
            return options[index]
    return stripped


def _handle_quiz_answer(state, reply_id, text):
    question_ids = state.context["question_ids"]
    index = state.context["index"]
    question = Question.objects.get(id=question_ids[index])

    student_answer = _resolve_quiz_answer(question, reply_id, text)
    is_correct = student_answer.strip().lower() == question.answer.strip().lower()

    answers = state.context.get("answers", [])
    answers.append({"question_id": str(question.id), "student_answer": student_answer})
    state.context["answers"] = answers

    feedback = (
        "✅ Correct!" if is_correct else f"❌ Incorrect. The correct answer is: {question.answer}"
    )
    if question.explanation:
        feedback += f"\n\n💡 {question.explanation}"

    next_index = index + 1
    if next_index >= len(question_ids):
        return [{"type": "text", "body": feedback}, *_finish_quiz(state)]

    state.context["index"] = next_index
    return [{"type": "text", "body": feedback}, *_send_quiz_question(state)]


def _finish_quiz(state):
    quiz = Quiz.objects.get(id=state.context["quiz_id"])
    attempt = quiz_services.submit_attempt(
        quiz=quiz, user=state.user, answers=state.context.get("answers", [])
    )
    weak_topics = list(
        dict.fromkeys(
            QuizAnswer.objects.filter(
                attempt=attempt, is_correct=False, question__topic__isnull=False
            ).values_list("question__topic__name", flat=True)
        )
    )[:3]

    body = f"🎉 Quiz complete! Score: {attempt.score}%"
    if weak_topics:
        body += "\n\n📌 Topics to review: " + ", ".join(weak_topics)

    return [{"type": "text", "body": body}, *_show_main_menu(state)]


# --- Progress flow --------------------------------------------------------------


def _progress_flow(state, *, text, reply_id):
    attempts = QuizAttempt.objects.filter(user=state.user, completed_at__isnull=False)
    total = attempts.count()
    if total == 0:
        body = "You haven't completed any quizzes yet. Try *Practice Quiz* from the main menu!"
        return [{"type": "text", "body": body}, *_show_main_menu(state)]

    avg_score = attempts.aggregate(avg=Avg("score"))["avg"] or 0
    recent_scores = list(attempts.order_by("-completed_at")[:5].values_list("score", flat=True))
    streak = StudyStreak.objects.filter(user=state.user).first()
    recommendations = list(
        Recommendation.objects.filter(user=state.user).select_related("topic")[:3]
    )

    body = (
        "📊 *My Progress*\n\n"
        f"Quizzes completed: {total}\n"
        f"Average score: {round(avg_score, 1)}%\n"
        f"Recent scores: {', '.join(f'{s}%' for s in recent_scores)}"
    )
    if streak and streak.current_streak > 0:
        body += f"\n🔥 Study streak: {streak.current_streak} day(s) (best: {streak.longest_streak})"
    actions = [{"type": "text", "body": body}]
    if recommendations:
        actions.append(
            {
                "type": "text",
                "body": "📌 " + "\n".join(rec.message for rec in recommendations),
            }
        )
    actions.extend(_show_main_menu(state))
    return actions


# --- AI Tutor flow -----------------------------------------------------------


def _ai_tutor_flow(state, *, text, reply_id):
    text = (text or "").strip()
    if not text:
        return [
            {
                "type": "text",
                "body": (
                    "🤖 *Ask AI Tutor*\nType your question about Maths, Science, or "
                    "any STEM topic and I'll do my best to help.\n\n"
                    "(Reply *menu* anytime to go back.)"
                ),
            }
        ]

    try:
        AccessGate.check(state.user, "ai_tutor")
    except AccessDenied as exc:
        return _start_billing_flow(state, exc.message)

    return [{"type": "enqueue_ai_tutor", "phone_number": state.phone_number, "question": text}]


# --- Billing / upgrade flow ---------------------------------------------------


def _start_billing_flow(state, denial_message):
    state.current_flow = ConversationState.Flow.BILLING
    state.current_step = "choose_plan"
    state.context = {}
    plans = list(Plan.objects.filter(is_active=True).exclude(code="free").order_by("price"))
    if not plans:
        state.reset_to_main_menu()
        return [{"type": "text", "body": denial_message}, *_show_main_menu(state)]

    rows = [
        {"id": f"plan_{plan.code}", "title": f"{plan.name} (${plan.price})"} for plan in plans
    ]
    return [
        {"type": "text", "body": f"🔒 {denial_message}\nUpgrade to keep going:"},
        {
            "type": "list",
            "body": "Choose a plan to subscribe:",
            "button_text": "Choose",
            "rows": rows,
            "section_title": "Plans",
        },
    ]


def _billing_flow(state, *, text, reply_id):
    step = state.current_step

    if step == "choose_plan":
        if not reply_id or not reply_id.startswith("plan_"):
            return [{"type": "text", "body": "Please choose a plan from the list above."}]
        plan_code = reply_id.removeprefix("plan_")
        if not Plan.objects.filter(code=plan_code, is_active=True).exists():
            return [{"type": "text", "body": "That plan isn't available. Please pick another."}]
        state.context["plan_code"] = plan_code
        state.current_step = "choose_method"
        return [
            {
                "type": "buttons",
                "body": "Which mobile money service would you like to pay with?",
                "buttons": [
                    {"id": "method_ecocash", "title": "EcoCash"},
                    {"id": "method_onemoney", "title": "OneMoney"},
                ],
            }
        ]

    if step == "choose_method":
        if reply_id not in ("method_ecocash", "method_onemoney"):
            return [{"type": "text", "body": "Please choose EcoCash or OneMoney."}]
        state.context["method"] = reply_id.removeprefix("method_")
        state.current_step = "enter_phone"
        return [
            {
                "type": "text",
                "body": "Enter the mobile money phone number to pay from (e.g. 0771234567):",
            }
        ]

    if step == "enter_phone":
        phone = (text or "").strip()
        if not phone or not phone.replace("+", "").isdigit():
            return [{"type": "text", "body": "Please enter a valid phone number."}]
        plan_code = state.context.get("plan_code")
        method = state.context.get("method")
        action = {
            "type": "enqueue_subscribe",
            "phone_number": state.phone_number,
            "user_id": str(state.user_id),
            "plan_code": plan_code,
            "method": method,
            "pay_phone": phone,
        }
        state.reset_to_main_menu()
        return [
            {
                "type": "text",
                "body": "📲 Sending you a payment prompt now, please check your phone...",
            },
            action,
        ]

    return _show_main_menu(state)


# --- Stubbed flows (backend not built yet) --------------------------------------


def _study_plan_flow(state, *, text, reply_id):
    body = (
        "🚧 *Study Plan* is launching in a future update. "
        "For now, try *Practice Quiz* or *Revision Notes* from the main menu."
    )
    return [{"type": "text", "body": body}, *_show_main_menu(state)]


_FLOW_HANDLERS = {
    ConversationState.Flow.MAIN_MENU: _show_main_menu,
    ConversationState.Flow.REGISTRATION: _registration_flow,
    ConversationState.Flow.PAST_PAPER: _past_paper_flow,
    ConversationState.Flow.REVISION: _revision_flow,
    ConversationState.Flow.QUIZ: _quiz_flow,
    ConversationState.Flow.AI_TUTOR: _ai_tutor_flow,
    ConversationState.Flow.STUDY_PLAN: _study_plan_flow,
    ConversationState.Flow.PROGRESS: _progress_flow,
    ConversationState.Flow.BILLING: _billing_flow,
}
