from rest_framework import serializers
from .models import Video, Frame, Annotation


class AnnotationSerializer(serializers.ModelSerializer):
    total_score = serializers.ReadOnlyField()
    pain_level = serializers.ReadOnlyField()
    facial_expression_display = serializers.CharField(source='get_facial_expression_display', read_only=True)
    cry_display = serializers.CharField(source='get_cry_display', read_only=True)
    breathing_pattern_display = serializers.CharField(source='get_breathing_pattern_display', read_only=True)
    arms_display = serializers.CharField(source='get_arms_display', read_only=True)
    legs_display = serializers.CharField(source='get_legs_display', read_only=True)
    state_of_arousal_display = serializers.CharField(source='get_state_of_arousal_display', read_only=True)

    class Meta:
        model = Annotation
        fields = [
            'id', 'frame', 'facial_expression', 'facial_expression_display',
            'cry', 'cry_display', 'breathing_pattern', 'breathing_pattern_display',
            'arms', 'arms_display', 'legs', 'legs_display',
            'state_of_arousal', 'state_of_arousal_display',
            'annotator_id', 'confidence', 'notes',
            'total_score', 'pain_level', 'created_at', 'updated_at'
        ]


class FrameSerializer(serializers.ModelSerializer):
    annotations = AnnotationSerializer(many=True, read_only=True)
    annotation_count = serializers.SerializerMethodField()

    class Meta:
        model = Frame
        fields = ['id', 'video', 'frame_number', 'timestamp_seconds', 'image_path', 'annotations', 'annotation_count']

    def get_annotation_count(self, obj):
        return obj.annotations.count()


class FrameListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing frames"""
    is_annotated = serializers.SerializerMethodField()

    class Meta:
        model = Frame
        fields = ['id', 'frame_number', 'timestamp_seconds', 'image_path', 'is_annotated']

    def get_is_annotated(self, obj):
        return obj.annotations.exists()


class VideoSerializer(serializers.ModelSerializer):
    annotation_progress = serializers.ReadOnlyField()
    frame_count = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'name', 'description', 'file_path', 'duration_seconds',
            'fps', 'total_frames', 'uploaded_at', 'subject_id',
            'recording_context', 'annotation_progress', 'frame_count'
        ]

    def get_frame_count(self, obj):
        return obj.frames.count()


class VideoDetailSerializer(VideoSerializer):
    frames = FrameListSerializer(many=True, read_only=True)

    class Meta(VideoSerializer.Meta):
        fields = VideoSerializer.Meta.fields + ['frames']


class StatisticsSerializer(serializers.Serializer):
    total_videos = serializers.IntegerField()
    total_frames = serializers.IntegerField()
    total_annotations = serializers.IntegerField()
    annotation_rate = serializers.FloatField()
    pain_distribution = serializers.DictField()
    score_distribution = serializers.ListField()
    annotations_by_context = serializers.DictField()
    recent_activity = serializers.ListField()
