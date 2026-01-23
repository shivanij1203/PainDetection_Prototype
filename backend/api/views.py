from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg
from django.db.models.functions import TruncDate
from .models import Video, Frame, Annotation
from .serializers import (
    VideoSerializer, VideoDetailSerializer, FrameSerializer,
    FrameListSerializer, AnnotationSerializer, StatisticsSerializer
)
import csv
import json
from django.http import HttpResponse
from .services.image_quality import get_analyzer
import cv2
import numpy as np
import base64


@api_view(['GET'])
def video_list(request):
    """List all videos"""
    videos = Video.objects.all()
    serializer = VideoSerializer(videos, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def video_detail(request, video_id):
    """Get video details with frames"""
    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        return Response({'error': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = VideoDetailSerializer(video)
    return Response(serializer.data)


@api_view(['GET'])
def frame_detail(request, frame_id):
    """Get frame with annotations"""
    try:
        frame = Frame.objects.get(id=frame_id)
    except Frame.DoesNotExist:
        return Response({'error': 'Frame not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = FrameSerializer(frame)
    return Response(serializer.data)


@api_view(['GET'])
def video_frames(request, video_id):
    """Get all frames for a video with pagination"""
    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        return Response({'error': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)

    # Pagination
    page = int(request.query_params.get('page', 1))
    per_page = int(request.query_params.get('per_page', 20))
    start = (page - 1) * per_page
    end = start + per_page

    frames = video.frames.all()[start:end]
    total = video.frames.count()

    serializer = FrameListSerializer(frames, many=True)
    return Response({
        'frames': serializer.data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@api_view(['POST'])
def create_annotation(request):
    """Create a new annotation for a frame"""
    serializer = AnnotationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def update_annotation(request, annotation_id):
    """Update an existing annotation"""
    try:
        annotation = Annotation.objects.get(id=annotation_id)
    except Annotation.DoesNotExist:
        return Response({'error': 'Annotation not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = AnnotationSerializer(annotation, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_annotation(request, annotation_id):
    """Delete an annotation"""
    try:
        annotation = Annotation.objects.get(id=annotation_id)
    except Annotation.DoesNotExist:
        return Response({'error': 'Annotation not found'}, status=status.HTTP_404_NOT_FOUND)

    annotation.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_statistics(request):
    """Get annotation statistics for dashboard"""
    total_videos = Video.objects.count()
    total_frames = Frame.objects.count()
    total_annotations = Annotation.objects.count()

    # Annotation rate
    annotation_rate = 0
    if total_frames > 0:
        annotated_frames = Frame.objects.filter(annotations__isnull=False).distinct().count()
        annotation_rate = round((annotated_frames / total_frames) * 100, 1)

    # Pain distribution
    pain_counts = {'no_pain': 0, 'mild_pain': 0, 'severe_pain': 0}
    for annotation in Annotation.objects.all():
        pain_counts[annotation.pain_level] += 1

    # Score distribution (0-7)
    score_dist = [0] * 8
    for annotation in Annotation.objects.all():
        score_dist[annotation.total_score] += 1

    # Annotations by context
    context_stats = {}
    for video in Video.objects.all():
        context = video.recording_context or 'unknown'
        if context not in context_stats:
            context_stats[context] = {'videos': 0, 'annotations': 0}
        context_stats[context]['videos'] += 1
        context_stats[context]['annotations'] += video.frames.filter(
            annotations__isnull=False
        ).distinct().count()

    # Recent activity (last 7 days)
    from datetime import timedelta
    from django.utils import timezone
    week_ago = timezone.now() - timedelta(days=7)
    recent = Annotation.objects.filter(created_at__gte=week_ago)\
        .annotate(date=TruncDate('created_at'))\
        .values('date')\
        .annotate(count=Count('id'))\
        .order_by('date')

    return Response({
        'total_videos': total_videos,
        'total_frames': total_frames,
        'total_annotations': total_annotations,
        'annotation_rate': annotation_rate,
        'pain_distribution': pain_counts,
        'score_distribution': score_dist,
        'annotations_by_context': context_stats,
        'recent_activity': list(recent)
    })


@api_view(['GET'])
def export_annotations(request, video_id):
    """Export annotations for a video as CSV"""
    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        return Response({'error': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)

    format_type = request.query_params.get('format', 'csv')

    annotations_data = []
    for frame in video.frames.all():
        for annotation in frame.annotations.all():
            annotations_data.append({
                'video_name': video.name,
                'subject_id': video.subject_id,
                'recording_context': video.recording_context,
                'frame_number': frame.frame_number,
                'timestamp_seconds': frame.timestamp_seconds,
                'facial_expression': annotation.facial_expression,
                'cry': annotation.cry,
                'breathing_pattern': annotation.breathing_pattern,
                'arms': annotation.arms,
                'legs': annotation.legs,
                'state_of_arousal': annotation.state_of_arousal,
                'total_score': annotation.total_score,
                'pain_level': annotation.pain_level,
                'confidence': annotation.confidence,
                'annotator_id': annotation.annotator_id,
                'notes': annotation.notes,
                'annotated_at': annotation.created_at.isoformat()
            })

    if format_type == 'json':
        response = HttpResponse(
            json.dumps(annotations_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{video.name}_annotations.json"'
    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{video.name}_annotations.csv"'

        if annotations_data:
            writer = csv.DictWriter(response, fieldnames=annotations_data[0].keys())
            writer.writeheader()
            writer.writerows(annotations_data)

    return response


@api_view(['GET'])
def get_nips_scale(request):
    """Return NIPS scale definitions for the frontend"""
    return Response({
        'name': 'Neonatal Infant Pain Scale (NIPS)',
        'description': 'A behavioral assessment tool for measuring pain in preterm and full-term neonates.',
        'score_range': {'min': 0, 'max': 7},
        'interpretation': {
            '0-2': 'No pain',
            '3-4': 'Mild pain',
            '5-7': 'Severe pain'
        },
        'components': {
            'facial_expression': {
                'label': 'Facial Expression',
                'max_score': 1,
                'options': [
                    {'value': 0, 'label': 'Relaxed muscles', 'description': 'Restful face, neutral expression'},
                    {'value': 1, 'label': 'Grimace', 'description': 'Tight facial muscles, furrowed brow, chin, jaw'}
                ]
            },
            'cry': {
                'label': 'Cry',
                'max_score': 2,
                'options': [
                    {'value': 0, 'label': 'No cry', 'description': 'Quiet, not crying'},
                    {'value': 1, 'label': 'Whimper', 'description': 'Mild moaning, intermittent'},
                    {'value': 2, 'label': 'Vigorous cry', 'description': 'Loud scream, shrill, continuous'}
                ]
            },
            'breathing_pattern': {
                'label': 'Breathing Pattern',
                'max_score': 1,
                'options': [
                    {'value': 0, 'label': 'Relaxed', 'description': 'Usual pattern for this infant'},
                    {'value': 1, 'label': 'Change in breathing', 'description': 'Irregular, faster than usual, gagging, breath holding'}
                ]
            },
            'arms': {
                'label': 'Arms',
                'max_score': 1,
                'options': [
                    {'value': 0, 'label': 'Relaxed/Restrained', 'description': 'No muscular rigidity, occasional random movements'},
                    {'value': 1, 'label': 'Flexed/Extended', 'description': 'Tense, straight arms, rigid and/or rapid extension, flexion'}
                ]
            },
            'legs': {
                'label': 'Legs',
                'max_score': 1,
                'options': [
                    {'value': 0, 'label': 'Relaxed/Restrained', 'description': 'No muscular rigidity, occasional random movements'},
                    {'value': 1, 'label': 'Flexed/Extended', 'description': 'Tense, straight legs, rigid and/or rapid extension, flexion'}
                ]
            },
            'state_of_arousal': {
                'label': 'State of Arousal',
                'max_score': 1,
                'options': [
                    {'value': 0, 'label': 'Sleeping/Awake', 'description': 'Quiet, peaceful, settled'},
                    {'value': 1, 'label': 'Fussy', 'description': 'Alert, restless, thrashing'}
                ]
            }
        }
    })


# ============================================
# IMAGE QUALITY & OCCLUSION ANALYSIS ENDPOINTS
# ============================================
# These endpoints address two key challenges from published research:
# 1. Dark images (pixel intensity ≤25) are unusable
# 2. Occlusion from medical equipment blocks faces

@api_view(['POST'])
def analyze_image(request):
    """
    Analyze a single image for quality and occlusion issues.

    Accepts either:
    - base64 encoded image in request body
    - file upload

    Returns comprehensive analysis addressing NICU-specific challenges.
    """
    analyzer = get_analyzer()

    # Check for base64 image
    if 'image' in request.data:
        base64_image = request.data['image']
        result = analyzer.analyze_from_base64(base64_image)
        return Response(result)

    # Check for file upload
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        file_bytes = uploaded_file.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return Response({'error': 'Failed to decode image'}, status=status.HTTP_400_BAD_REQUEST)

        result = analyzer.analyze_image(image)
        return Response(result)

    return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def analyze_batch(request):
    """
    Analyze multiple images in batch.

    Useful for pre-screening a dataset before annotation.
    Returns summary statistics and individual results.
    """
    analyzer = get_analyzer()

    images = request.data.get('images', [])

    if not images:
        return Response({'error': 'No images provided'}, status=status.HTTP_400_BAD_REQUEST)

    results = []
    summary = {
        'total': len(images),
        'usable': 0,
        'marginal': 0,
        'unusable': 0,
        'issues': {
            'too_dark': 0,
            'too_bright': 0,
            'blurry': 0,
            'low_contrast': 0,
            'no_face': 0,
            'occluded': 0
        }
    }

    for i, base64_image in enumerate(images):
        result = analyzer.analyze_from_base64(base64_image)
        result['index'] = i
        results.append(result)

        # Update summary
        if 'error' not in result:
            usability = result['overall']['usability']
            summary[usability] += 1

            quality = result['quality']
            if quality['brightness']['is_too_dark']:
                summary['issues']['too_dark'] += 1
            if quality['brightness']['is_too_bright']:
                summary['issues']['too_bright'] += 1
            if quality['blur']['is_blurry']:
                summary['issues']['blurry'] += 1
            if quality['contrast']['is_low_contrast']:
                summary['issues']['low_contrast'] += 1

            occlusion = result['occlusion']
            if not occlusion['face_detected']:
                summary['issues']['no_face'] += 1
            elif occlusion['occlusion_level'] in ['partial', 'severe']:
                summary['issues']['occluded'] += 1

    return Response({
        'summary': summary,
        'results': results
    })


@api_view(['GET'])
def get_quality_thresholds(request):
    """
    Return the quality thresholds used for analysis.

    Based on findings from:
    "Accurate Neonatal Face Detection for Improved Pain Classification
    in the Challenging NICU Setting" (IEEE Access, 2024)
    """
    from .services.image_quality import ImageQualityAnalyzer

    return Response({
        'thresholds': {
            'brightness': {
                'dark_threshold': ImageQualityAnalyzer.DARK_THRESHOLD,
                'bright_threshold': ImageQualityAnalyzer.BRIGHT_THRESHOLD,
                'description': 'Images with pixel intensity ≤25 are unusable per research findings'
            },
            'blur': {
                'threshold': ImageQualityAnalyzer.BLUR_THRESHOLD,
                'method': 'Laplacian variance',
                'description': 'Lower values indicate more blur'
            },
            'contrast': {
                'threshold': ImageQualityAnalyzer.CONTRAST_THRESHOLD,
                'method': 'Standard deviation of pixel values',
                'description': 'Low contrast makes facial features hard to distinguish'
            },
            'resolution': {
                'minimum': ImageQualityAnalyzer.MIN_RESOLUTION,
                'description': 'Minimum dimension in pixels for reliable face detection'
            }
        },
        'references': [
            {
                'title': 'Accurate Neonatal Face Detection for Improved Pain Classification in the Challenging NICU Setting',
                'journal': 'IEEE Access',
                'year': 2024,
                'finding': 'Images with average pixel intensity of 25 or lower are unusable'
            }
        ]
    })


# ============================================
# VIDEO PROCESSING ENDPOINTS
# ============================================
# Bridges the gap between video input and frame-by-frame analysis

@api_view(['POST'])
def analyze_video(request):
    """
    Upload and analyze a video file.

    Extracts frames at 1 fps (configurable) and runs quality analysis
    on each frame automatically.

    Returns:
    - Video metadata (duration, fps, frame count)
    - Summary (usable/marginal/unusable counts)
    - Frame-by-frame results with thumbnails
    - List of usable frame indices for annotation
    """
    from .services.video_processor import get_processor

    if 'file' not in request.FILES:
        return Response({'error': 'No video file provided'}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']

    # Get extraction rate from request (default: 1 fps)
    extraction_fps = float(request.data.get('extraction_fps', 1.0))

    processor = get_processor(extraction_fps)
    video_bytes = uploaded_file.read()

    result = processor.process_video_bytes(video_bytes, uploaded_file.name)

    if 'error' in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    return Response(result)
