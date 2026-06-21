from django.contrib import admin

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "topic", "subtopic")
    list_filter = ("subject", "topic")
    search_fields = ("title", "content")
