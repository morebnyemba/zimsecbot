from django.contrib import admin

from .models import KnowledgeChunk, KnowledgeDocument


class KnowledgeChunkInline(admin.TabularInline):
    model = KnowledgeChunk
    extra = 0
    fields = ("chunk_index", "text")
    readonly_fields = ("chunk_index", "text")


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "source_type", "subject", "topic", "indexed_at")
    list_filter = ("source_type", "subject")
    search_fields = ("title",)
    inlines = [KnowledgeChunkInline]
