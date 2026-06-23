from django.contrib import admin

from .models import Recommendation, StudyStreak, TopicPerformance


@admin.register(TopicPerformance)
class TopicPerformanceAdmin(admin.ModelAdmin):
    list_display = ("user", "subject", "topic", "attempts_count", "accuracy")
    list_filter = ("subject",)


@admin.register(StudyStreak)
class StudyStreakAdmin(admin.ModelAdmin):
    list_display = ("user", "current_streak", "longest_streak", "last_activity_date")


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("user", "subject", "topic", "reason", "created_at")
    list_filter = ("reason", "subject")
