from django.urls import path
from . import views

urlpatterns = [
    # Videos
    path('videos/', views.video_list, name='video_list'),
    path('videos/<uuid:video_id>/', views.video_detail, name='video_detail'),
    path('videos/<uuid:video_id>/frames/', views.video_frames, name='video_frames'),
    path('videos/<uuid:video_id>/export/', views.export_annotations, name='export_annotations'),

    # Frames
    path('frames/<uuid:frame_id>/', views.frame_detail, name='frame_detail'),

    # Annotations
    path('annotations/', views.create_annotation, name='create_annotation'),
    path('annotations/<uuid:annotation_id>/', views.update_annotation, name='update_annotation'),
    path('annotations/<uuid:annotation_id>/delete/', views.delete_annotation, name='delete_annotation'),

    # Statistics & Reference
    path('statistics/', views.get_statistics, name='statistics'),
    path('nips-scale/', views.get_nips_scale, name='nips_scale'),

    # Image Quality & Occlusion Analysis
    # Addresses challenges from published research
    path('analyze/image/', views.analyze_image, name='analyze_image'),
    path('analyze/batch/', views.analyze_batch, name='analyze_batch'),
    path('analyze/thresholds/', views.get_quality_thresholds, name='quality_thresholds'),

    # Video Processing
    # Upload video → Extract frames → Analyze each → Get usable frames
    path('analyze/video/', views.analyze_video, name='analyze_video'),
]
