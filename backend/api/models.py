from django.db import models
import uuid

class Video(models.Model):
    """Represents an uploaded video for annotation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file_path = models.CharField(max_length=500)
    duration_seconds = models.FloatField(null=True, blank=True)
    fps = models.FloatField(default=30.0)
    total_frames = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Metadata
    subject_id = models.CharField(max_length=100, blank=True, help_text="Anonymous subject identifier")
    recording_context = models.CharField(max_length=100, blank=True,
        help_text="e.g., baseline, heel_lance, immunization, post_operative")

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name

    @property
    def annotation_progress(self):
        total = self.frames.count()
        if total == 0:
            return 0
        annotated = self.frames.filter(annotations__isnull=False).distinct().count()
        return round((annotated / total) * 100, 1)


class Frame(models.Model):
    """Individual frame extracted from a video"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='frames')
    frame_number = models.IntegerField()
    timestamp_seconds = models.FloatField()
    image_path = models.CharField(max_length=500)

    class Meta:
        ordering = ['video', 'frame_number']
        unique_together = ['video', 'frame_number']

    def __str__(self):
        return f"{self.video.name} - Frame {self.frame_number}"


class Annotation(models.Model):
    """NIPS-based pain annotation for a frame"""

    # NIPS scoring options
    FACIAL_CHOICES = [
        (0, 'Relaxed muscles - Restful face, neutral expression'),
        (1, 'Grimace - Tight facial muscles, furrowed brow, chin, jaw'),
    ]

    CRY_CHOICES = [
        (0, 'No cry - Quiet, not crying'),
        (1, 'Whimper - Mild moaning, intermittent'),
        (2, 'Vigorous cry - Loud scream, shrill, continuous'),
    ]

    BREATHING_CHOICES = [
        (0, 'Relaxed - Usual pattern for this infant'),
        (1, 'Change in breathing - Irregular, faster than usual, gagging, breath holding'),
    ]

    ARMS_CHOICES = [
        (0, 'Relaxed/Restrained - No muscular rigidity, occasional random movements'),
        (1, 'Flexed/Extended - Tense, straight arms, rigid and/or rapid extension, flexion'),
    ]

    LEGS_CHOICES = [
        (0, 'Relaxed/Restrained - No muscular rigidity, occasional random movements'),
        (1, 'Flexed/Extended - Tense, straight legs, rigid and/or rapid extension, flexion'),
    ]

    STATE_CHOICES = [
        (0, 'Sleeping/Awake - Quiet, peaceful, settled'),
        (1, 'Fussy - Alert, restless, thrashing'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    frame = models.ForeignKey(Frame, on_delete=models.CASCADE, related_name='annotations')

    # NIPS components
    facial_expression = models.IntegerField(choices=FACIAL_CHOICES)
    cry = models.IntegerField(choices=CRY_CHOICES)
    breathing_pattern = models.IntegerField(choices=BREATHING_CHOICES)
    arms = models.IntegerField(choices=ARMS_CHOICES)
    legs = models.IntegerField(choices=LEGS_CHOICES)
    state_of_arousal = models.IntegerField(choices=STATE_CHOICES)

    # Metadata
    annotator_id = models.CharField(max_length=100, help_text="Anonymous annotator identifier")
    confidence = models.CharField(max_length=20, choices=[
        ('high', 'High - Clear indicators'),
        ('medium', 'Medium - Some uncertainty'),
        ('low', 'Low - Difficult to assess'),
    ], default='medium')
    notes = models.TextField(blank=True, help_text="Any observations or difficulties")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['frame__video', 'frame__frame_number', '-created_at']

    def __str__(self):
        return f"Annotation for {self.frame} by {self.annotator_id}"

    @property
    def total_score(self):
        """Calculate total NIPS score (0-7)"""
        return (
            self.facial_expression +
            self.cry +
            self.breathing_pattern +
            self.arms +
            self.legs +
            self.state_of_arousal
        )

    @property
    def pain_level(self):
        """Interpret NIPS score"""
        score = self.total_score
        if score <= 2:
            return 'no_pain'
        elif score <= 4:
            return 'mild_pain'
        else:
            return 'severe_pain'
