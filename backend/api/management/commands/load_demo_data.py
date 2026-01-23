from django.core.management.base import BaseCommand
from api.models import Video, Frame, Annotation
import random

class Command(BaseCommand):
    help = 'Load demo data for the annotation tool'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')

        # Clear existing data
        Annotation.objects.all().delete()
        Frame.objects.all().delete()
        Video.objects.all().delete()

        # Demo videos representing different clinical scenarios
        videos_data = [
            {
                'name': 'Subject_001_Baseline',
                'description': 'Baseline recording before any procedure',
                'subject_id': 'NEO-001',
                'recording_context': 'baseline',
                'fps': 30,
                'duration_seconds': 60,
            },
            {
                'name': 'Subject_001_HeelLance',
                'description': 'Recording during heel lance blood draw',
                'subject_id': 'NEO-001',
                'recording_context': 'heel_lance',
                'fps': 30,
                'duration_seconds': 120,
            },
            {
                'name': 'Subject_002_Baseline',
                'description': 'Baseline recording - quiet state',
                'subject_id': 'NEO-002',
                'recording_context': 'baseline',
                'fps': 30,
                'duration_seconds': 45,
            },
            {
                'name': 'Subject_002_PostOp',
                'description': 'Post-operative monitoring',
                'subject_id': 'NEO-002',
                'recording_context': 'post_operative',
                'fps': 30,
                'duration_seconds': 180,
            },
            {
                'name': 'Subject_003_Immunization',
                'description': 'Recording during immunization',
                'subject_id': 'NEO-003',
                'recording_context': 'immunization',
                'fps': 30,
                'duration_seconds': 90,
            },
        ]

        for video_data in videos_data:
            video = Video.objects.create(
                name=video_data['name'],
                description=video_data['description'],
                file_path=f"/demo/videos/{video_data['name']}.mp4",
                subject_id=video_data['subject_id'],
                recording_context=video_data['recording_context'],
                fps=video_data['fps'],
                duration_seconds=video_data['duration_seconds'],
            )

            # Extract frames at 1 fps for annotation (not every frame)
            num_frames = int(video_data['duration_seconds'])
            video.total_frames = num_frames

            for i in range(num_frames):
                Frame.objects.create(
                    video=video,
                    frame_number=i,
                    timestamp_seconds=float(i),
                    image_path=f"/demo/frames/{video_data['name']}/frame_{i:04d}.jpg"
                )

            video.save()
            self.stdout.write(f'  Created video: {video.name} with {num_frames} frames')

        # Add some sample annotations to show the tool in action
        annotator_ids = ['annotator_A', 'annotator_B']

        # Baseline videos should have low pain scores
        baseline_videos = Video.objects.filter(recording_context='baseline')
        for video in baseline_videos:
            frames = list(video.frames.all()[:10])  # Annotate first 10 frames
            for frame in frames:
                Annotation.objects.create(
                    frame=frame,
                    facial_expression=random.choice([0, 0, 0, 1]),  # Mostly relaxed
                    cry=0,
                    breathing_pattern=0,
                    arms=0,
                    legs=0,
                    state_of_arousal=random.choice([0, 0, 1]),
                    annotator_id=random.choice(annotator_ids),
                    confidence='high',
                    notes=''
                )

        # Painful procedures should have higher scores
        painful_videos = Video.objects.filter(
            recording_context__in=['heel_lance', 'immunization', 'post_operative']
        )
        for video in painful_videos:
            frames = list(video.frames.all()[:15])
            for i, frame in enumerate(frames):
                # Pain increases during procedure, then decreases
                if i < 5:  # Before peak
                    pain_level = 'low'
                elif i < 10:  # During peak
                    pain_level = 'high'
                else:  # Recovery
                    pain_level = 'medium'

                if pain_level == 'low':
                    facial = random.choice([0, 1])
                    cry = random.choice([0, 1])
                    breathing = random.choice([0, 1])
                    arms = 0
                    legs = 0
                    state = random.choice([0, 1])
                elif pain_level == 'high':
                    facial = 1
                    cry = random.choice([1, 2])
                    breathing = 1
                    arms = random.choice([0, 1])
                    legs = random.choice([0, 1])
                    state = 1
                else:
                    facial = random.choice([0, 1])
                    cry = random.choice([0, 1])
                    breathing = random.choice([0, 1])
                    arms = 0
                    legs = 0
                    state = random.choice([0, 1])

                Annotation.objects.create(
                    frame=frame,
                    facial_expression=facial,
                    cry=cry,
                    breathing_pattern=breathing,
                    arms=arms,
                    legs=legs,
                    state_of_arousal=state,
                    annotator_id=random.choice(annotator_ids),
                    confidence=random.choice(['high', 'medium', 'medium']),
                    notes='' if random.random() > 0.2 else 'Partial face occlusion'
                )

        total_videos = Video.objects.count()
        total_frames = Frame.objects.count()
        total_annotations = Annotation.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f'Demo data loaded: {total_videos} videos, {total_frames} frames, {total_annotations} annotations'
        ))
