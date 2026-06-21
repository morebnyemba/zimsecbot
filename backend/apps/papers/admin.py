from django.contrib import admin

from .models import MarkingScheme, PastPaper


@admin.register(MarkingScheme)
class MarkingSchemeAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(PastPaper)
class PastPaperAdmin(admin.ModelAdmin):
    list_display = ("subject", "year", "session", "paper_number", "paper_type")
    list_filter = ("subject", "year", "paper_type", "session")
