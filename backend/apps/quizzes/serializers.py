from rest_framework import serializers

from apps.questions.models import Question

from .models import Quiz, QuizAnswer, QuizAttempt, QuizQuestion


class QuizQuestionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="question.id")
    question_text = serializers.CharField(source="question.question_text")
    question_type = serializers.CharField(source="question.question_type")
    options = serializers.JSONField(source="question.options")
    marks = serializers.IntegerField(source="question.marks")

    class Meta:
        model = QuizQuestion
        fields = ["id", "question_text", "question_type", "options", "marks"]


class QuizSerializer(serializers.ModelSerializer):
    quiz_questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id", "subject", "topic", "difficulty", "source_channel",
            "created_at", "quiz_questions",
        ]


class QuizGenerateSerializer(serializers.Serializer):
    subject_id = serializers.UUIDField()
    topic_id = serializers.UUIDField(required=False, allow_null=True)
    difficulty = serializers.CharField(required=False, allow_blank=True)
    question_count = serializers.IntegerField(min_value=1, max_value=50, default=10)


class AnswerInputSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    student_answer = serializers.CharField(allow_blank=True)


class AttemptSubmitSerializer(serializers.Serializer):
    answers = AnswerInputSerializer(many=True)


class QuizAnswerResultSerializer(serializers.ModelSerializer):
    explanation = serializers.CharField(source="question.explanation", read_only=True)

    class Meta:
        model = QuizAnswer
        fields = ["question_id", "is_correct", "marks_awarded", "explanation"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = QuizAnswerResultSerializer(many=True, read_only=True)
    total_marks = serializers.SerializerMethodField()
    marks_awarded = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = [
            "id", "quiz", "score", "total_marks", "marks_awarded",
            "started_at", "completed_at", "answers",
        ]

    def get_total_marks(self, obj):
        return sum(
            Question.objects.filter(id__in=obj.answers.values_list("question_id", flat=True))
            .values_list("marks", flat=True)
        )

    def get_marks_awarded(self, obj):
        return sum(obj.answers.values_list("marks_awarded", flat=True))
