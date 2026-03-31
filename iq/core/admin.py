from django.contrib import admin
from .models import AcademicNote, NoteSummary, ImportantQuestion, ContentAnalysis

@admin.register(AcademicNote)
class AcademicNoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploaded_by', 'uploaded_at', 'updated_at']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['title', 'content']
    readonly_fields = ['uploaded_at', 'updated_at']

@admin.register(NoteSummary)
class NoteSummaryAdmin(admin.ModelAdmin):
    list_display = ['note', 'generated_at']
    search_fields = ['note__title']

@admin.register(ImportantQuestion)
class ImportantQuestionAdmin(admin.ModelAdmin):
    list_display = ['note', 'difficulty', 'created_at']
    list_filter = ['difficulty', 'created_at']
    search_fields = ['question_text']

@admin.register(ContentAnalysis)
class ContentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['note', 'clarity_score', 'structure_score', 'analyzed_at']
    list_filter = ['analyzed_at']