from django.contrib import admin

from .models import StudentSubject, Subject, Subtopic, Topic


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 0


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "level", "tier", "is_active")
    list_filter = ("level", "tier", "is_active")
    search_fields = ("name", "code")
    inlines = [TopicInline]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "order")
    list_filter = ("subject",)


@admin.register(Subtopic)
class SubtopicAdmin(admin.ModelAdmin):
    list_display = ("name", "topic", "order")


@admin.register(StudentSubject)
class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = ("user", "subject")
