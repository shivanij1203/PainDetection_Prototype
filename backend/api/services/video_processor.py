"""
Video Processing Service for NICU Pain Detection

Handles:
1. Video upload and storage
2. Frame extraction at configurable intervals
3. Automatic quality analysis on each frame
4. Filtering usable frames for annotation

This bridges the gap between video input and image-based quality analysis.
"""

import cv2
import numpy as np
import os
import uuid
import base64
from typing import List, Dict, Tuple
from dataclasses import dataclass
from .image_quality import get_analyzer


@dataclass
class FrameResult:
    """Result for a single extracted frame"""
    frame_number: int
    timestamp_seconds: float
    quality_score: float
    usability: str  # usable, marginal, unusable
    brightness: float
    is_too_dark: bool
    is_blurry: bool
    face_detected: bool
    occlusion_level: str
    thumbnail_base64: str  # Small preview


@dataclass
class VideoAnalysisResult:
    """Complete analysis result for a video"""
    video_id: str
    filename: str
    duration_seconds: float
    fps: float
    total_frames_extracted: int

    # Summary counts
    usable_count: int
    marginal_count: int
    unusable_count: int

    # Issue counts
    too_dark_count: int
    blurry_count: int
    no_face_count: int
    occluded_count: int

    # All frame results
    frames: List[FrameResult]

    # Usable frame indices for annotation
    usable_frame_indices: List[int]


class VideoProcessor:
    """
    Processes NICU videos for quality analysis.

    Workflow:
    1. Upload video
    2. Extract frames at specified interval
    3. Analyze each frame for quality/occlusion
    4. Apply adjacent frame smoothing for borderline detections
    5. Return summary + frame-by-frame results
    """

    def __init__(self, extraction_fps: float = 1.0):
        """
        Args:
            extraction_fps: Frames to extract per second (default: 1 fps)
        """
        self.extraction_fps = extraction_fps
        self.analyzer = get_analyzer()
        self.thumbnail_size = (120, 90)  # Small preview size

    def _apply_adjacent_frame_smoothing(self, frame_results: List[dict]) -> List[dict]:
        """
        Apply temporal smoothing by considering adjacent frames.

        If a frame has uncertain or no face detection, but its neighbors
        have good face detection, boost the frame's usability.

        This addresses the issue where very similar consecutive frames
        get drastically different scores due to borderline face detection.
        """
        if len(frame_results) < 3:
            return frame_results

        smoothed_results = []

        for i, frame in enumerate(frame_results):
            # Get adjacent frames
            prev_frame = frame_results[i - 1] if i > 0 else None
            next_frame = frame_results[i + 1] if i < len(frame_results) - 1 else None

            # Check if current frame has poor face detection
            current_face_status = frame.get('face_detection_status', 'not_detected')
            current_usability = frame.get('usability')

            # Count how many adjacent frames have face detection (detected or uncertain)
            adjacent_detected_count = 0  # Fully detected faces
            adjacent_any_face_count = 0  # Any face evidence (detected or uncertain)
            adjacent_scores = []

            if prev_frame:
                prev_status = prev_frame.get('face_detection_status', 'not_detected')
                if prev_status == 'detected':
                    adjacent_detected_count += 1
                    adjacent_any_face_count += 1
                    adjacent_scores.append(prev_frame.get('quality_score', 0))
                elif prev_status == 'uncertain':
                    adjacent_any_face_count += 1
                    adjacent_scores.append(prev_frame.get('quality_score', 0))

            if next_frame:
                next_status = next_frame.get('face_detection_status', 'not_detected')
                if next_status == 'detected':
                    adjacent_detected_count += 1
                    adjacent_any_face_count += 1
                    adjacent_scores.append(next_frame.get('quality_score', 0))
                elif next_status == 'uncertain':
                    adjacent_any_face_count += 1
                    adjacent_scores.append(next_frame.get('quality_score', 0))

            # Apply smoothing if current frame is uncertain/not_detected but neighbors have face evidence
            smoothed_frame = frame.copy()

            if current_face_status in ['not_detected', 'uncertain'] and adjacent_any_face_count >= 1:
                # Boost the frame based on adjacent frame evidence
                avg_adjacent_score = sum(adjacent_scores) / len(adjacent_scores) if adjacent_scores else 0

                if current_face_status == 'not_detected' and adjacent_any_face_count == 2:
                    # Both neighbors have face evidence - likely a momentary detection failure
                    smoothed_frame['adjacent_boost'] = True
                    smoothed_frame['original_usability'] = current_usability
                    smoothed_frame['original_score'] = frame.get('quality_score', 0)

                    # Boost score based on neighbor quality
                    # Stronger boost if neighbors are "detected", moderate if "uncertain"
                    boost_factor = 0.6 if adjacent_detected_count >= 1 else 0.5
                    boosted_score = frame.get('quality_score', 0) * (1 - boost_factor) + avg_adjacent_score * boost_factor
                    smoothed_frame['quality_score'] = round(boosted_score, 1)

                    # Upgrade usability
                    if boosted_score >= 70:
                        smoothed_frame['usability'] = 'usable'
                    elif boosted_score >= 45:
                        smoothed_frame['usability'] = 'marginal'

                    smoothed_frame['issues'] = [
                        issue for issue in frame.get('issues', [])
                        if 'Face not detected' not in issue
                    ]
                    smoothed_frame['issues'].append('Face detection boosted by adjacent frames')

                elif current_face_status == 'not_detected' and adjacent_any_face_count == 1:
                    # One neighbor has face evidence - moderate boost
                    smoothed_frame['adjacent_boost'] = True
                    smoothed_frame['original_usability'] = current_usability
                    smoothed_frame['original_score'] = frame.get('quality_score', 0)

                    boosted_score = frame.get('quality_score', 0) * 0.6 + avg_adjacent_score * 0.4
                    smoothed_frame['quality_score'] = round(boosted_score, 1)

                    if boosted_score >= 70:
                        smoothed_frame['usability'] = 'usable'
                    elif boosted_score >= 45:
                        smoothed_frame['usability'] = 'marginal'

                    smoothed_frame['issues'] = [
                        issue for issue in frame.get('issues', [])
                        if 'Face not detected' not in issue
                    ]
                    smoothed_frame['issues'].append('Face detection partially boosted by adjacent frame')

                elif current_face_status == 'uncertain' and adjacent_any_face_count >= 1:
                    # Uncertain detection with at least one neighbor having face evidence
                    smoothed_frame['adjacent_boost'] = True
                    smoothed_frame['original_usability'] = current_usability
                    smoothed_frame['original_score'] = frame.get('quality_score', 0)

                    # Moderate boost
                    boosted_score = frame.get('quality_score', 0) * 0.7 + avg_adjacent_score * 0.3
                    smoothed_frame['quality_score'] = round(boosted_score, 1)

                    if boosted_score >= 70:
                        smoothed_frame['usability'] = 'usable'
                    elif boosted_score >= 45:
                        smoothed_frame['usability'] = 'marginal'

                    smoothed_frame['issues'] = [
                        issue for issue in frame.get('issues', [])
                        if 'borderline' not in issue.lower()
                    ]
                    smoothed_frame['issues'].append('Uncertain detection confirmed by adjacent frames')

            smoothed_results.append(smoothed_frame)

        return smoothed_results

    def process_video_file(self, video_path: str) -> Dict:
        """
        Process a video file from disk.

        Args:
            video_path: Path to video file

        Returns:
            Complete analysis result as dictionary
        """
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return {"error": f"Failed to open video: {video_path}"}

        return self._process_video_capture(cap, os.path.basename(video_path))

    def process_video_bytes(self, video_bytes: bytes, filename: str) -> Dict:
        """
        Process video from bytes (uploaded file).

        Args:
            video_bytes: Raw video bytes
            filename: Original filename

        Returns:
            Complete analysis result as dictionary
        """
        # Save temporarily to process with OpenCV
        temp_path = f"/tmp/video_{uuid.uuid4().hex}.mp4"

        try:
            with open(temp_path, 'wb') as f:
                f.write(video_bytes)

            cap = cv2.VideoCapture(temp_path)

            if not cap.isOpened():
                return {"error": "Failed to decode video"}

            result = self._process_video_capture(cap, filename)

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return result

    def _process_video_capture(self, cap: cv2.VideoCapture, filename: str) -> Dict:
        """
        Internal method to process an opened video capture.
        """
        video_id = str(uuid.uuid4())

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        # Calculate frame extraction interval
        frame_interval = int(fps / self.extraction_fps) if self.extraction_fps < fps else 1

        # Process frames
        frame_results = []
        frame_number = 0
        extracted_count = 0

        # Counters
        usable_count = 0
        marginal_count = 0
        unusable_count = 0
        too_dark_count = 0
        blurry_count = 0
        no_face_count = 0
        occluded_count = 0
        usable_indices = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Only process frames at the extraction interval
            if frame_number % frame_interval == 0:
                timestamp = frame_number / fps

                # Analyze frame
                analysis = self.analyzer.analyze_image(frame)

                # Create thumbnail
                thumbnail = cv2.resize(frame, self.thumbnail_size)
                _, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 70])
                thumbnail_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"

                # Extract key metrics
                quality = analysis['quality']
                occlusion = analysis['occlusion']
                overall = analysis['overall']

                frame_result = {
                    'frame_number': extracted_count,
                    'original_frame': frame_number,
                    'timestamp_seconds': round(timestamp, 2),
                    'quality_score': overall['score'],
                    'usability': overall['usability'],
                    'brightness': quality['brightness']['mean'],
                    'is_too_dark': quality['brightness']['is_too_dark'],
                    'is_blurry': quality['blur']['is_blurry'],
                    'face_detected': occlusion['face_detected'],
                    'face_detection_status': occlusion.get('face_detection_status', 'detected' if occlusion['face_detected'] else 'not_detected'),
                    'face_confidence': occlusion['confidence'],
                    'occlusion_level': occlusion['occlusion_level'],
                    'thumbnail': thumbnail_base64,
                    'issues': overall['issues'],
                    'recommendations': overall['recommendations']
                }

                frame_results.append(frame_result)

                # Update counters
                if overall['usability'] == 'usable':
                    usable_count += 1
                    usable_indices.append(extracted_count)
                elif overall['usability'] == 'marginal':
                    marginal_count += 1
                else:
                    unusable_count += 1

                if quality['brightness']['is_too_dark']:
                    too_dark_count += 1
                if quality['blur']['is_blurry']:
                    blurry_count += 1
                if not occlusion['face_detected']:
                    no_face_count += 1
                elif occlusion['occlusion_level'] in ['partial', 'severe']:
                    occluded_count += 1

                extracted_count += 1

            frame_number += 1

        cap.release()

        # Apply adjacent frame smoothing to handle borderline face detection
        smoothed_frames = self._apply_adjacent_frame_smoothing(frame_results)

        # Recalculate summary based on smoothed results
        usable_count = 0
        marginal_count = 0
        unusable_count = 0
        usable_indices = []

        for i, frame in enumerate(smoothed_frames):
            if frame['usability'] == 'usable':
                usable_count += 1
                usable_indices.append(i)
            elif frame['usability'] == 'marginal':
                marginal_count += 1
            else:
                unusable_count += 1

        # Count boosted frames for transparency
        boosted_count = sum(1 for f in smoothed_frames if f.get('adjacent_boost', False))

        return {
            'video_id': video_id,
            'filename': filename,
            'duration_seconds': round(duration, 2),
            'fps': round(fps, 2),
            'total_frames_in_video': total_frames,
            'total_frames_extracted': extracted_count,
            'extraction_fps': self.extraction_fps,

            'summary': {
                'usable': usable_count,
                'marginal': marginal_count,
                'unusable': unusable_count,
                'usable_percentage': round(usable_count / extracted_count * 100, 1) if extracted_count > 0 else 0,
                'boosted_by_adjacent': boosted_count  # Frames improved by temporal smoothing
            },

            'issues': {
                'too_dark': too_dark_count,
                'blurry': blurry_count,
                'no_face': no_face_count,
                'occluded': occluded_count
            },

            'frames': smoothed_frames,
            'usable_frame_indices': usable_indices,

            'recommendation': self._generate_recommendation(
                usable_count, marginal_count, unusable_count,
                too_dark_count, blurry_count, no_face_count
            )
        }

    def _generate_recommendation(self, usable, marginal, unusable,
                                  too_dark, blurry, no_face) -> str:
        """Generate overall recommendation based on analysis."""
        total = usable + marginal + unusable
        usable_pct = usable / total * 100 if total > 0 else 0

        if usable_pct >= 80:
            return "Good quality video. Most frames are suitable for annotation."
        elif usable_pct >= 50:
            rec = "Moderate quality. "
            if too_dark > unusable * 0.5:
                rec += "Consider improving lighting conditions. "
            if blurry > unusable * 0.5:
                rec += "Camera focus or motion blur issues detected. "
            return rec + f"{usable} frames are ready for annotation."
        else:
            rec = "Quality issues detected. "
            if too_dark > total * 0.3:
                rec += "CRITICAL: Lighting is too dark in many frames. "
            if no_face > total * 0.3:
                rec += "Face detection failing frequently - check camera angle and occlusion. "
            return rec + "Consider re-recording or adjusting NICU camera setup."


# Singleton instance
_processor = None

def get_processor(extraction_fps: float = 1.0) -> VideoProcessor:
    global _processor
    if _processor is None or _processor.extraction_fps != extraction_fps:
        _processor = VideoProcessor(extraction_fps)
    return _processor
