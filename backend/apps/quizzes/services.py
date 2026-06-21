import random

from django.utils import timezone

from apps.questions.models import Question

from .models import Quiz, QuizAnswer, QuizAttempt, QuizQuestion


def generate_quiz(*, user, subject_id, topic_id=None, difficulty=None, question_count=10):
    questions = Question.objects.filter(subject_id=subject_id)
    if topic_id:
        questions = questions.filter(topic_id=topic_id)
    if difficulty:
        questions = questions.filter(difficulty=difficulty)

    question_ids = list(questions.values_list("id", flat=True))
    random.shuffle(question_ids)
    selected_ids = question_ids[:question_count]

    quiz = Quiz.objects.create(
        created_by=user,
        subject_id=subject_id,
        topic_id=topic_id,
        difficulty=difficulty or "",
    )
    QuizQuestion.objects.bulk_create(
        [
            QuizQuestion(quiz=quiz, question_id=question_id, order=order)
            for order, question_id in enumerate(selected_ids)
        ]
    )
    return quiz


def submit_attempt(*, quiz, user, answers):
    attempt = QuizAttempt.objects.create(quiz=quiz, user=user)
    quiz_question_ids = set(
        QuizQuestion.objects.filter(quiz=quiz).values_list("question_id", flat=True)
    )
    questions_by_id = {q.id: q for q in Question.objects.filter(id__in=quiz_question_ids)}

    total_marks = 0
    marks_awarded = 0
    quiz_answers = []
    for answer in answers:
        question = questions_by_id.get(answer["question_id"])
        if question is None:
            continue
        student_answer = answer.get("student_answer", "")
        is_correct = student_answer.strip().lower() == question.answer.strip().lower()
        awarded = question.marks if is_correct else 0
        total_marks += question.marks
        marks_awarded += awarded
        quiz_answers.append(
            QuizAnswer(
                attempt=attempt,
                question=question,
                student_answer=student_answer,
                is_correct=is_correct,
                marks_awarded=awarded,
            )
        )
    QuizAnswer.objects.bulk_create(quiz_answers)

    attempt.score = round((marks_awarded / total_marks) * 100, 2) if total_marks else 0.0
    attempt.completed_at = timezone.now()
    attempt.save(update_fields=["score", "completed_at"])
    return attempt
