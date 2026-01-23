"""
Image Quality Analysis for NICU Neonatal Pain Detection

This module addresses two key challenges identified in published research:
1. Image quality issues (dark images with pixel intensity ≤25 are unusable)
2. Occlusion from medical equipment blocking infant faces

References:
- "Accurate Neonatal Face Detection for Improved Pain Classification
   in the Challenging NICU Setting" (IEEE Access, 2024)
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Optional
import base64
from io import BytesIO


@dataclass
class QualityMetrics:
    """Container for image quality analysis results"""
    # Brightness metrics
    mean_brightness: float
    brightness_std: float
    is_too_dark: bool  # Paper threshold: ≤25 pixel intensity
    is_too_bright: bool

    # Blur metrics
    laplacian_variance: float
    is_blurry: bool

    # Contrast metrics
    contrast_score: float
    is_low_contrast: bool

    # Resolution metrics
    width: int
    height: int
    resolution_adequate: bool

    # Overall
    overall_score: float  # 0-100
    usability: str  # "usable", "marginal", "unusable"
    issues: List[str]
    recommendations: List[str]


@dataclass
class OcclusionMetrics:
    """Container for face/occlusion analysis results"""
    face_detected: bool
    face_detection_status: str  # "detected", "uncertain", "not_detected"
    num_faces: int
    face_confidence: float
    face_bbox: Optional[Tuple[int, int, int, int]]  # x, y, w, h

    # Landmark analysis
    landmarks_detected: bool
    landmarks_visible: int
    landmarks_expected: int
    landmark_visibility_ratio: float

    # Occlusion assessment
    occlusion_score: float  # 0-100, higher = more occluded
    occlusion_level: str  # "none", "partial", "severe"
    likely_causes: List[str]

    # Overall
    face_usable: bool
    recommendations: List[str]


class ImageQualityAnalyzer:
    """
    Analyzes image quality for NICU neonatal pain detection research.

    Addresses the challenge that "images with average pixel intensity
    of 25 or lower" are unusable for annotation and model training.
    """

    # Thresholds based on research paper findings
    DARK_THRESHOLD = 25  # From paper: pixel intensity ≤25 unusable
    BRIGHT_THRESHOLD = 240
    BLUR_THRESHOLD = 100  # Laplacian variance threshold
    CONTRAST_THRESHOLD = 30
    MIN_RESOLUTION = 64  # Minimum face size in pixels

    def analyze(self, image: np.ndarray) -> QualityMetrics:
        """
        Perform comprehensive quality analysis on an image.

        Args:
            image: BGR image as numpy array (OpenCV format)

        Returns:
            QualityMetrics with detailed analysis results
        """
        # Convert to grayscale for analysis
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        issues = []
        recommendations = []

        # 1. Brightness Analysis
        mean_brightness = np.mean(gray)
        brightness_std = np.std(gray)
        is_too_dark = mean_brightness <= self.DARK_THRESHOLD
        is_too_bright = mean_brightness >= self.BRIGHT_THRESHOLD

        if is_too_dark:
            issues.append(f"Image too dark (intensity: {mean_brightness:.1f}, threshold: {self.DARK_THRESHOLD})")
            recommendations.append("Improve lighting conditions during capture")
            recommendations.append("Consider histogram equalization preprocessing")
        elif is_too_bright:
            issues.append(f"Image overexposed (intensity: {mean_brightness:.1f})")
            recommendations.append("Reduce lighting or camera exposure")

        # 2. Blur Detection (Laplacian variance method)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_variance = laplacian.var()
        is_blurry = laplacian_variance < self.BLUR_THRESHOLD

        if is_blurry:
            issues.append(f"Image is blurry (sharpness: {laplacian_variance:.1f}, threshold: {self.BLUR_THRESHOLD})")
            recommendations.append("Ensure camera is focused properly")
            recommendations.append("Reduce motion blur with faster shutter speed")

        # 3. Contrast Analysis
        contrast_score = brightness_std
        is_low_contrast = contrast_score < self.CONTRAST_THRESHOLD

        if is_low_contrast:
            issues.append(f"Low contrast (score: {contrast_score:.1f})")
            recommendations.append("Apply contrast enhancement (CLAHE)")

        # 4. Resolution Check
        height, width = gray.shape[:2]
        min_dimension = min(width, height)
        resolution_adequate = min_dimension >= self.MIN_RESOLUTION

        if not resolution_adequate:
            issues.append(f"Resolution too low ({width}x{height})")
            recommendations.append("Use higher resolution camera or move closer")

        # Calculate overall score (0-100)
        score = 100.0

        # Brightness penalty
        if is_too_dark:
            score -= min(40, (self.DARK_THRESHOLD - mean_brightness) * 2)
        elif is_too_bright:
            score -= min(30, (mean_brightness - self.BRIGHT_THRESHOLD) / 2)
        else:
            # Optimal range bonus
            optimal_brightness = 128
            brightness_deviation = abs(mean_brightness - optimal_brightness)
            score -= min(10, brightness_deviation / 20)

        # Blur penalty
        if is_blurry:
            score -= min(30, (self.BLUR_THRESHOLD - laplacian_variance) / 5)

        # Contrast penalty
        if is_low_contrast:
            score -= min(20, (self.CONTRAST_THRESHOLD - contrast_score))

        # Resolution penalty
        if not resolution_adequate:
            score -= 20

        overall_score = max(0, min(100, score))

        # Determine usability
        if overall_score >= 70:
            usability = "usable"
        elif overall_score >= 40:
            usability = "marginal"
        else:
            usability = "unusable"

        if not recommendations:
            recommendations.append("Image quality is acceptable for annotation")

        return QualityMetrics(
            mean_brightness=mean_brightness,
            brightness_std=brightness_std,
            is_too_dark=is_too_dark,
            is_too_bright=is_too_bright,
            laplacian_variance=laplacian_variance,
            is_blurry=is_blurry,
            contrast_score=contrast_score,
            is_low_contrast=is_low_contrast,
            width=width,
            height=height,
            resolution_adequate=resolution_adequate,
            overall_score=overall_score,
            usability=usability,
            issues=issues,
            recommendations=recommendations
        )


class OcclusionAnalyzer:
    """
    Analyzes face visibility and occlusion in NICU images.

    Addresses the challenge that "occlusion from medical equipment"
    is a major obstacle in neonatal face detection.
    """

    def __init__(self):
        # Initialize face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        # Try to load MediaPipe for better face mesh detection
        self.mp_face_mesh = None
        self.mp_face_detection = None
        try:
            import mediapipe as mp
            self.mp_face_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.3
            )
            self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                min_detection_confidence=0.3,
                min_tracking_confidence=0.3
            )
        except Exception as e:
            print(f"MediaPipe not available, using OpenCV fallback: {e}")

    # Confidence thresholds for face detection status
    CONFIDENCE_DETECTED = 0.5      # Above this = "detected"
    CONFIDENCE_UNCERTAIN = 0.2     # Between uncertain and detected = "uncertain"
    # Below CONFIDENCE_UNCERTAIN = "not_detected"

    def analyze(self, image: np.ndarray) -> OcclusionMetrics:
        """
        Analyze face visibility and potential occlusion.

        Args:
            image: BGR image as numpy array

        Returns:
            OcclusionMetrics with face detection and occlusion analysis
        """
        issues = []
        recommendations = []

        face_detected = False
        face_detection_status = "not_detected"
        num_faces = 0
        face_confidence = 0.0
        face_bbox = None
        landmarks_detected = False
        landmarks_visible = 0
        landmarks_expected = 468  # MediaPipe face mesh landmarks

        # Track detections from multiple methods for better accuracy
        mediapipe_confidence = 0.0
        haar_detected = False

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Try MediaPipe first (better for neonates)
        if self.mp_face_detection:
            results = self.mp_face_detection.process(rgb_image)

            if results.detections:
                num_faces = len(results.detections)
                detection = results.detections[0]
                mediapipe_confidence = detection.score[0]
                face_confidence = mediapipe_confidence

                # Get bounding box
                bbox = detection.location_data.relative_bounding_box
                h, w = image.shape[:2]
                face_bbox = (
                    int(bbox.xmin * w),
                    int(bbox.ymin * h),
                    int(bbox.width * w),
                    int(bbox.height * h)
                )

                if mediapipe_confidence >= self.CONFIDENCE_DETECTED:
                    face_detected = True
                    face_detection_status = "detected"
                elif mediapipe_confidence >= self.CONFIDENCE_UNCERTAIN:
                    face_detected = True
                    face_detection_status = "uncertain"

        # Also try OpenCV Haar cascades (as supporting evidence)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30)
        )
        haar_detected = len(faces) > 0

        # If MediaPipe missed but Haar found a face, mark as uncertain
        if not face_detected and haar_detected:
            face_detected = True
            face_detection_status = "uncertain"
            num_faces = len(faces)
            face_confidence = 0.35  # Lower confidence for Haar-only detection
            x, y, w, h = faces[0]
            face_bbox = (x, y, w, h)

        # If MediaPipe was uncertain but Haar confirms, boost confidence
        elif face_detection_status == "uncertain" and haar_detected:
            face_confidence = min(0.6, face_confidence + 0.15)  # Boost for dual detection
            if face_confidence >= self.CONFIDENCE_DETECTED:
                face_detection_status = "detected"

        # Landmark analysis with MediaPipe Face Mesh
        if face_detected and self.mp_face_mesh:
            mesh_results = self.mp_face_mesh.process(rgb_image)

            if mesh_results.multi_face_landmarks:
                landmarks_detected = True
                face_landmarks = mesh_results.multi_face_landmarks[0]

                # Count visible landmarks (visibility > 0.5)
                # MediaPipe provides visibility for some landmarks
                landmarks_visible = len(face_landmarks.landmark)

                # Check key facial regions
                # Simplified: just count total landmarks detected
                landmarks_expected = 468

        # Calculate landmark visibility ratio
        if landmarks_detected:
            landmark_visibility_ratio = landmarks_visible / landmarks_expected
        else:
            landmark_visibility_ratio = 0.0 if face_detected else 0.0

        # Determine occlusion level based on face_detection_status
        likely_causes = []

        if face_detection_status == "not_detected":
            occlusion_score = 100.0
            occlusion_level = "severe"
            likely_causes.append("Face not detected - possibly fully occluded")
            likely_causes.append("May be due to medical equipment (tubes, tape, monitors)")
            likely_causes.append("Extreme head pose or face out of frame")
            recommendations.append("Reposition camera or wait for clearer view")
            recommendations.append("Check for equipment obstruction")
        elif face_detection_status == "uncertain":
            # New category: face might be there but detection is borderline
            occlusion_score = 50.0
            occlusion_level = "uncertain"
            likely_causes.append("Face detection borderline - may need manual review")
            likely_causes.append("Could be slight head turn, motion blur, or partial occlusion")
            recommendations.append("Consider checking adjacent frames")
            recommendations.append("May be usable with manual verification")
        elif face_confidence < 0.6:
            occlusion_score = 40.0
            occlusion_level = "partial"
            likely_causes.append("Low detection confidence suggests partial occlusion")
            likely_causes.append("Possible causes: CPAP mask, nasal cannula, medical tape")
            recommendations.append("Frame may still be usable but flag for manual review")
        elif landmark_visibility_ratio < 0.7:
            occlusion_score = 30.0
            occlusion_level = "partial"
            likely_causes.append("Some facial landmarks not visible")
            likely_causes.append("Partial equipment occlusion or head rotation")
            recommendations.append("Consider for annotation with 'partial visibility' flag")
        else:
            occlusion_score = max(0, (1 - face_confidence) * 20)
            occlusion_level = "none"
            recommendations.append("Face clearly visible - suitable for annotation")

        # Determine if face is usable - uncertain is now potentially usable
        face_usable = face_detected and occlusion_level not in ["severe"]

        return OcclusionMetrics(
            face_detected=face_detected,
            face_detection_status=face_detection_status,
            num_faces=num_faces,
            face_confidence=face_confidence,
            face_bbox=face_bbox,
            landmarks_detected=landmarks_detected,
            landmarks_visible=landmarks_visible,
            landmarks_expected=landmarks_expected,
            landmark_visibility_ratio=landmark_visibility_ratio,
            occlusion_score=occlusion_score,
            occlusion_level=occlusion_level,
            likely_causes=likely_causes,
            face_usable=face_usable,
            recommendations=recommendations
        )


class NICUImageAnalyzer:
    """
    Combined analyzer for NICU neonatal pain detection research.
    Addresses key challenges from published literature.
    """

    def __init__(self):
        self.quality_analyzer = ImageQualityAnalyzer()
        self.occlusion_analyzer = OcclusionAnalyzer()

    def analyze_image(self, image: np.ndarray) -> dict:
        """
        Perform complete analysis on a NICU image.

        Returns combined quality and occlusion metrics with
        overall usability assessment.
        """
        quality = self.quality_analyzer.analyze(image)
        occlusion = self.occlusion_analyzer.analyze(image)

        # Combined assessment
        all_issues = quality.issues.copy()
        all_recommendations = []

        if occlusion.likely_causes:
            all_issues.extend(occlusion.likely_causes)

        # Prioritize recommendations
        if quality.is_too_dark:
            all_recommendations.append("CRITICAL: Image too dark for reliable analysis")
        if occlusion.face_detection_status == "not_detected":
            all_recommendations.append("CRITICAL: No face detected - check for occlusion")
        elif occlusion.face_detection_status == "uncertain":
            all_recommendations.append("Face detection uncertain - may need manual review")

        all_recommendations.extend(quality.recommendations)
        all_recommendations.extend(occlusion.recommendations)

        # Overall usability - with less harsh penalties for uncertain detection
        if quality.usability == "unusable" or occlusion.face_detection_status == "not_detected":
            overall_usability = "unusable"
            overall_score = min(quality.overall_score, 35)
        elif occlusion.face_detection_status == "uncertain":
            # Uncertain face detection: marginal but not unusable
            overall_usability = "marginal"
            # Less harsh penalty: quality score weighted more heavily
            overall_score = quality.overall_score * 0.7 + (100 - occlusion.occlusion_score) * 0.3
        elif quality.usability == "marginal" or occlusion.occlusion_level == "partial":
            overall_usability = "marginal"
            overall_score = (quality.overall_score + (100 - occlusion.occlusion_score)) / 2
        else:
            overall_usability = "usable"
            overall_score = (quality.overall_score + (100 - occlusion.occlusion_score)) / 2

        return {
            "quality": {
                "brightness": {
                    "mean": round(quality.mean_brightness, 2),
                    "std": round(quality.brightness_std, 2),
                    "is_too_dark": quality.is_too_dark,
                    "is_too_bright": quality.is_too_bright,
                    "threshold_dark": ImageQualityAnalyzer.DARK_THRESHOLD,
                },
                "blur": {
                    "laplacian_variance": round(quality.laplacian_variance, 2),
                    "is_blurry": quality.is_blurry,
                    "threshold": ImageQualityAnalyzer.BLUR_THRESHOLD,
                },
                "contrast": {
                    "score": round(quality.contrast_score, 2),
                    "is_low_contrast": quality.is_low_contrast,
                },
                "resolution": {
                    "width": quality.width,
                    "height": quality.height,
                    "adequate": quality.resolution_adequate,
                },
                "overall_score": round(quality.overall_score, 1),
                "usability": quality.usability,
            },
            "occlusion": {
                "face_detected": occlusion.face_detected,
                "face_detection_status": occlusion.face_detection_status,  # "detected", "uncertain", "not_detected"
                "num_faces": occlusion.num_faces,
                "confidence": round(occlusion.face_confidence, 3),
                "bbox": occlusion.face_bbox,
                "landmarks": {
                    "detected": occlusion.landmarks_detected,
                    "visible": occlusion.landmarks_visible,
                    "expected": occlusion.landmarks_expected,
                    "visibility_ratio": round(occlusion.landmark_visibility_ratio, 3),
                },
                "occlusion_score": round(occlusion.occlusion_score, 1),
                "occlusion_level": occlusion.occlusion_level,
                "likely_causes": occlusion.likely_causes,
                "face_usable": occlusion.face_usable,
            },
            "overall": {
                "score": round(overall_score, 1),
                "usability": overall_usability,
                "issues": all_issues,
                "recommendations": all_recommendations[:5],  # Top 5
            }
        }

    def analyze_from_base64(self, base64_string: str) -> dict:
        """Analyze image from base64 encoded string."""
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]

        image_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return {"error": "Failed to decode image"}

        return self.analyze_image(image)

    def analyze_from_file(self, file_path: str) -> dict:
        """Analyze image from file path."""
        image = cv2.imread(file_path)

        if image is None:
            return {"error": f"Failed to load image from {file_path}"}

        return self.analyze_image(image)


# Singleton instance
_analyzer = None

def get_analyzer() -> NICUImageAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = NICUImageAnalyzer()
    return _analyzer
