import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.questions.models import Question
from apps.subjects.models import Subject

from .engine import HELP_TEXT, handle_inbound_message
from .models import ConversationState

User = get_user_model()


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="student@example.com", password="testpass123", phone_number="+263771234567"
    )


@pytest.fixture
def state(student):
    return ConversationState.objects.create(phone_number="+263771234567", user=student)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)


@pytest.fixture
def mcq_question(subject):
    return Question.objects.create(
        subject=subject,
        question_type=Question.QuestionType.MCQ,
        difficulty=Question.Difficulty.EASY,
        question_text="2 + 2 = ?",
        options=["3", "4", "5"],
        answer="4",
        explanation="Basic arithmetic.",
        marks=1,
    )


@pytest.mark.django_db
def test_new_phone_number_triggers_registration():
    state = ConversationState.objects.create(phone_number="+263770000000")
    actions = handle_inbound_message(state, text="hi", reply_id=None)
    state.save()
    assert state.current_flow == ConversationState.Flow.REGISTRATION
    assert "name" in actions[0]["body"].lower()


@pytest.mark.django_db
def test_registration_creates_user_and_links_phone():
    state = ConversationState.objects.create(phone_number="+263770000001")
    handle_inbound_message(state, text="hi", reply_id=None)
    state.save()

    handle_inbound_message(state, text="Tendai Moyo", reply_id=None)
    state.save()
    assert state.current_step == "ask_email"

    actions = handle_inbound_message(state, text="tendai@example.com", reply_id=None)
    state.save()

    state.refresh_from_db()
    assert state.user is not None
    assert state.user.email == "tendai@example.com"
    assert state.user.first_name == "Tendai"
    assert state.user.phone_number == "+263770000001"
    assert state.current_flow == ConversationState.Flow.MAIN_MENU
    assert any("welcome" in a["body"].lower() for a in actions)


@pytest.mark.django_db
def test_help_command_does_not_change_flow(state):
    state.current_flow = ConversationState.Flow.QUIZ
    state.current_step = "choose_subject"
    state.save()

    actions = handle_inbound_message(state, text="help", reply_id=None)
    state.save()

    assert actions == [{"type": "text", "body": HELP_TEXT}]
    state.refresh_from_db()
    assert state.current_flow == ConversationState.Flow.QUIZ


@pytest.mark.django_db
def test_menu_command_resets_to_main_menu(state):
    state.current_flow = ConversationState.Flow.REVISION
    state.current_step = "choose_topic"
    state.context = {"subject_id": "abc"}
    state.save()

    handle_inbound_message(state, text="menu", reply_id=None)
    state.save()

    state.refresh_from_db()
    assert state.current_flow == ConversationState.Flow.MAIN_MENU
    assert state.context == {}


@pytest.mark.django_db
def test_timeout_resets_mid_flow_state(state):
    state.current_flow = ConversationState.Flow.QUIZ
    state.current_step = "choose_subject"
    state.save()
    ConversationState.objects.filter(pk=state.pk).update(
        updated_at=timezone.now() - timezone.timedelta(hours=2)
    )
    state.refresh_from_db()

    handle_inbound_message(state, text="anything", reply_id=None)
    state.save()

    state.refresh_from_db()
    assert state.current_flow == ConversationState.Flow.MAIN_MENU


@pytest.mark.django_db
def test_main_menu_routes_to_quiz_flow(state, subject):
    handle_inbound_message(state, text="", reply_id=None)
    state.save()

    actions = handle_inbound_message(state, text="", reply_id="menu_quiz")
    state.save()

    state.refresh_from_db()
    assert state.current_flow == ConversationState.Flow.QUIZ
    assert state.current_step == "choose_subject"
    assert actions[0]["type"] == "list"


@pytest.mark.django_db
def test_full_quiz_flow_happy_path(state, subject, mcq_question):
    handle_inbound_message(state, text="", reply_id=None)
    state.save()
    handle_inbound_message(state, text="", reply_id="menu_quiz")
    state.save()

    handle_inbound_message(state, text="", reply_id=f"subject_{subject.id}")
    state.save()
    assert state.current_step == "choose_topic"

    handle_inbound_message(state, text="", reply_id="topic_none")
    state.save()
    assert state.current_step == "choose_difficulty"

    handle_inbound_message(state, text="", reply_id="difficulty_easy")
    state.save()
    assert state.current_step == "question"
    assert state.context["question_ids"] == [str(mcq_question.id)]

    actions = handle_inbound_message(state, text="", reply_id="answer_1")
    state.save()

    state.refresh_from_db()
    assert any("correct" in a["body"].lower() for a in actions if a["type"] == "text")
    assert state.current_flow == ConversationState.Flow.MAIN_MENU


@pytest.mark.django_db
def test_ai_tutor_prompts_for_question(state):
    handle_inbound_message(state, text="", reply_id=None)
    state.save()

    actions = handle_inbound_message(state, text="", reply_id="menu_ai_tutor")
    state.save()

    assert "ask ai tutor" in actions[0]["body"].lower()
    state.refresh_from_db()
    assert state.current_flow == ConversationState.Flow.AI_TUTOR
    assert state.current_step == "ask"


@pytest.mark.django_db
def test_ai_tutor_question_enqueues_action(state):
    state.current_flow = ConversationState.Flow.AI_TUTOR
    state.current_step = "ask"
    state.save()

    actions = handle_inbound_message(state, text="What is photosynthesis?", reply_id=None)

    assert actions == [
        {
            "type": "enqueue_ai_tutor",
            "phone_number": state.phone_number,
            "question": "What is photosynthesis?",
        }
    ]


@pytest.mark.django_db
def test_ai_tutor_over_quota_starts_billing_flow(state):
    from apps.billing.models import UsageRecord

    UsageRecord.objects.create(
        user=state.user, feature_key="ai_tutor", count=5, period_date=timezone.localdate()
    )
    state.current_flow = ConversationState.Flow.AI_TUTOR
    state.current_step = "ask"
    state.save()

    actions = handle_inbound_message(state, text="What is photosynthesis?", reply_id=None)
    state.save()

    assert any(a["type"] == "list" for a in actions)
    state.refresh_from_db()
    assert state.current_flow == ConversationState.Flow.BILLING
    assert state.current_step == "choose_plan"


@pytest.mark.django_db
def test_billing_flow_collects_plan_method_and_phone(state):
    state.current_flow = ConversationState.Flow.BILLING
    state.current_step = "choose_plan"
    state.save()

    actions = handle_inbound_message(state, text="", reply_id="plan_plus")
    state.save()
    state.refresh_from_db()
    assert state.current_step == "choose_method"
    assert any(a["type"] == "buttons" for a in actions)

    handle_inbound_message(state, text="", reply_id="method_ecocash")
    state.save()
    state.refresh_from_db()
    assert state.current_step == "enter_phone"

    actions = handle_inbound_message(state, text="0771234567", reply_id=None)
    state.save()
    state.refresh_from_db()

    assert state.current_flow == ConversationState.Flow.MAIN_MENU
    enqueue_actions = [a for a in actions if a["type"] == "enqueue_subscribe"]
    assert len(enqueue_actions) == 1
    assert enqueue_actions[0]["plan_code"] == "plus"
    assert enqueue_actions[0]["method"] == "ecocash"
    assert enqueue_actions[0]["pay_phone"] == "0771234567"
