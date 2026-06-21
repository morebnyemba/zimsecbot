from django.contrib import admin

from .models import Quiz, QuizAnswer, QuizAttempt, QuizQuestion


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "topic", "difficulty", "source_channel", "created_at")
    list_filter = ("subject", "difficulty", "source_channel")
    inlines = [QuizQuestionInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quiz", "score", "started_at", "completed_at")
    list_filter = ("quiz__subject",)


admin.site.register(QuizAnswer)
