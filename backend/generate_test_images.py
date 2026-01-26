"""
Generate sample test images demonstrating NICU image quality issues.

Creates synthetic images that simulate common problems:
1. Too dark (pixel intensity ≤25)
2. Too bright (overexposed)
3. Blurry
4. Low contrast
5. Good quality (for comparison)

These are NOT real neonatal images - they are synthetic test cases
to demonstrate the quality analyzer functionality.
"""

import cv2
import numpy as np
import os

OUTPUT_DIR = 'test_images'

def create_base_image(size=(400, 400)):
    """Create a base synthetic face-like image"""
    img = np.ones((size[0], size[1], 3), dtype=np.uint8) * 180

    # Simple face shape (oval)
    center = (size[1] // 2, size[0] // 2)
    cv2.ellipse(img, center, (80, 100), 0, 0, 360, (220, 200, 190), -1)

    # Eyes
    cv2.circle(img, (center[0] - 30, center[1] - 20), 12, (60, 60, 60), -1)
    cv2.circle(img, (center[0] + 30, center[1] - 20), 12, (60, 60, 60), -1)

    # Nose
    pts = np.array([[center[0], center[1]], [center[0] - 8, center[1] + 25],
                    [center[0] + 8, center[1] + 25]], np.int32)
    cv2.fillPoly(img, [pts], (200, 180, 170))

    # Mouth
    cv2.ellipse(img, (center[0], center[1] + 45), (20, 8), 0, 0, 180, (150, 100, 100), -1)

    return img


def create_dark_image():
    """Create an image that's too dark (simulating NICU lighting issues)"""
    img = create_base_image()
    # Reduce brightness significantly
    dark = (img * 0.1).astype(np.uint8)
    return dark


def create_very_dark_image():
    """Create an image below the ≤25 threshold"""
    img = create_base_image()
    # Make it extremely dark
    very_dark = (img * 0.05).astype(np.uint8)
    return very_dark


def create_bright_image():
    """Create an overexposed image"""
    img = create_base_image()
    # Increase brightness
    bright = cv2.convertScaleAbs(img, alpha=1.8, beta=80)
    return bright


def create_blurry_image():
    """Create a blurry image (simulating motion blur or focus issues)"""
    img = create_base_image()
    # Apply Gaussian blur
    blurry = cv2.GaussianBlur(img, (31, 31), 0)
    return blurry


def create_low_contrast_image():
    """Create a low contrast image"""
    img = create_base_image()
    # Reduce contrast
    low_contrast = cv2.convertScaleAbs(img, alpha=0.3, beta=100)
    return low_contrast


def create_occluded_image():
    """Create an image with simulated medical equipment occlusion"""
    img = create_base_image()

    # Simulate nasal cannula / tubes
    cv2.line(img, (120, 220), (280, 220), (100, 100, 100), 8)
    cv2.line(img, (150, 220), (150, 280), (100, 100, 100), 6)
    cv2.line(img, (250, 220), (250, 280), (100, 100, 100), 6)

    # Simulate tape
    cv2.rectangle(img, (160, 180), (240, 200), (255, 250, 230), -1)

    return img


def create_partial_face_image():
    """Create an image with face partially out of frame"""
    img = create_base_image((400, 400))
    # Crop to show only part of the face
    partial = img[100:400, 50:350]
    return partial


def create_good_image():
    """Create a good quality image for comparison"""
    img = create_base_image()
    # Slight enhancement for better quality
    enhanced = cv2.convertScaleAbs(img, alpha=1.1, beta=10)
    return enhanced


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    test_cases = [
        ('good_quality.jpg', create_good_image(), 'Good quality - should pass all checks'),
        ('too_dark.jpg', create_dark_image(), 'Too dark - simulates poor NICU lighting'),
        ('very_dark_below_threshold.jpg', create_very_dark_image(), 'Below ≤25 threshold - unusable per research'),
        ('overexposed.jpg', create_bright_image(), 'Overexposed - too bright'),
        ('blurry.jpg', create_blurry_image(), 'Motion blur - common in active infants'),
        ('low_contrast.jpg', create_low_contrast_image(), 'Low contrast - hard to distinguish features'),
        ('occluded_equipment.jpg', create_occluded_image(), 'Medical equipment occlusion'),
        ('partial_face.jpg', create_partial_face_image(), 'Partial face visibility'),
    ]

    print(f"Generating {len(test_cases)} test images in '{OUTPUT_DIR}/'...")

    for filename, image, description in test_cases:
        filepath = os.path.join(OUTPUT_DIR, filename)
        cv2.imwrite(filepath, image)
        print(f"  Created: {filename} - {description}")

    print("\nTest images generated successfully!")
    print(f"Location: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == '__main__':
    main()
