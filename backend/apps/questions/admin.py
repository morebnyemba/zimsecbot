from django.contrib import admin

from .models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("subject", "topic", "question_type", "difficulty", "marks")
    list_filter = ("subject", "topic", "question_type", "difficulty")
    search_fields = ("question_text",)
