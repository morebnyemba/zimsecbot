from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse

from apps.subjects.models import Subject, Subtopic, Topic

from .ingestion import ExtractionError, extract_pdf_text, extract_url_text
from .models import Note


class NoteImportForm(forms.Form):
    subject = forms.ModelChoiceField(queryset=Subject.objects.all())
    topic = forms.ModelChoiceField(queryset=Topic.objects.all(), required=False)
    subtopic = forms.ModelChoiceField(queryset=Subtopic.objects.all(), required=False)
    title = forms.CharField(max_length=255)
    source_url = forms.URLField(
        required=False,
        label="Web page URL",
        help_text="Paste a URL to import an article from.",
        assume_scheme="https",
    )
    source_file = forms.FileField(
        required=False, label="PDF file", help_text="...or upload a PDF instead."
    )

    def clean(self):
        cleaned = super().clean()
        url = cleaned.get("source_url")
        file = cleaned.get("source_file")
        if not url and not file:
            raise forms.ValidationError("Provide either a URL or a PDF file.")
        if url and file:
            raise forms.ValidationError("Provide only one of URL or PDF file, not both.")
        return cleaned


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "topic", "status", "source")
    list_filter = ("status", "subject", "topic")
    search_fields = ("title", "content")
    actions = ["mark_published", "mark_draft"]
    change_list_template = "notes/note_change_list.html"

    @admin.action(description="Mark selected notes as Published (indexes them)")
    def mark_published(self, request, queryset):
        count = 0
        for note in queryset:
            note.status = Note.Status.PUBLISHED
            note.save(update_fields=["status", "updated_at"])
            count += 1
        self.message_user(request, f"Published {count} note(s).", messages.SUCCESS)

    @admin.action(description="Mark selected notes as Draft (removes from knowledge base)")
    def mark_draft(self, request, queryset):
        count = 0
        for note in queryset:
            note.status = Note.Status.DRAFT
            note.save(update_fields=["status", "updated_at"])
            count += 1
        self.message_user(request, f"Marked {count} note(s) as draft.", messages.SUCCESS)

    def get_urls(self):
        urls = [
            path(
                "import/",
                self.admin_site.admin_view(self.import_view),
                name="notes_note_import",
            ),
        ]
        return urls + super().get_urls()

    def import_view(self, request):
        if request.method == "POST":
            form = NoteImportForm(request.POST, request.FILES)
            if form.is_valid():
                data = form.cleaned_data
                try:
                    if data.get("source_file"):
                        content = extract_pdf_text(data["source_file"])
                        source = data["source_file"].name
                    else:
                        content = extract_url_text(data["source_url"])
                        source = data["source_url"]
                except ExtractionError as exc:
                    form.add_error(None, str(exc))
                else:
                    note = Note.objects.create(
                        subject=data["subject"],
                        topic=data.get("topic"),
                        subtopic=data.get("subtopic"),
                        title=data["title"],
                        content=content,
                        status=Note.Status.DRAFT,
                        source=source,
                    )
                    self.message_user(
                        request,
                        f"Created draft note '{note.title}' ({len(content)} chars extracted). "
                        f"Review the content below, then mark it Published.",
                        messages.SUCCESS,
                    )
                    return redirect(
                        reverse("admin:notes_note_change", args=[note.pk])
                    )
        else:
            form = NoteImportForm()

        return render(
            request,
            "notes/note_import.html",
            {**self.admin_site.each_context(request), "form": form, "title": "Import Note"},
        )
