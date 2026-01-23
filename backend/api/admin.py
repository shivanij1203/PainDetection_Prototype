from django.contrib import admin
from .models import Video, Frame, Annotation

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject_id', 'recording_context', 'total_frames', 'uploaded_at']
    search_fields = ['name', 'subject_id']
    list_filter = ['recording_context']

@admin.register(Frame)
class FrameAdmin(admin.ModelAdmin):
    list_display = ['video', 'frame_number', 'timestamp_seconds']
    list_filter = ['video']

@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ['frame', 'total_score', 'pain_level', 'annotator_id', 'confidence', 'created_at']
    list_filter = ['confidence', 'annotator_id']
