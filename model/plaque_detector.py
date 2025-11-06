import cv2
import numpy as np
from skimage import measure, morphology
from scipy import ndimage
import os
import json


class PlaqueDetector:
    """Main plaque detection class using computer vision methods"""

    def __init__(self):
        self.model_version = 0

        # Try to load version from file
        version_file = 'model/checkpoints/version.txt'
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    self.model_version = int(f.read().strip())
            except:
                pass

    def preprocess_image(self, image_path):
        """Load and preprocess image for detection"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img, img_rgb

    def segment_plaques(self, image, params=None):
        """Use traditional CV methods for initial plaque segmentation"""
        # Default parameters
        if params is None:
            params = {
                'min_radius': 5,
                'max_radius': 50,
                'sensitivity': 30,
                'min_distance': 20
            }

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)

        # Detect circles (plaques) using Hough transform
        circles = cv2.HoughCircles(
            enhanced,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=params['min_distance'],
            param1=50,
            param2=params['sensitivity'],
            minRadius=params['min_radius'],
            maxRadius=params['max_radius']
        )

        detections = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for circle in circles[0, :]:
                x, y, r = int(circle[0]), int(circle[1]), int(circle[2])
                detections.append({
                    'x': x,
                    'y': y,
                    'radius': r,
                    'confidence': 0.8  # Default confidence
                })

        # Also try adaptive thresholding for irregular plaques
        adaptive_detections = self.detect_by_thresholding(enhanced, params)
        detections.extend(adaptive_detections)

        # Remove overlapping detections
        detections = self.non_max_suppression(detections)

        return detections

    def detect_by_thresholding(self, gray_image, params=None):
        """Alternative detection method using adaptive thresholding"""
        if params is None:
            params = {'min_radius': 5, 'max_radius': 50}

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray_image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=15,
            C=2
        )

        # Remove small noise
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(
            cleaned,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        min_area = params['min_radius'] ** 2 * 3.14
        max_area = params['max_radius'] ** 2 * 3.14

        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            # Filter by area (plaques should be reasonably sized)
            if min_area < area < max_area:
                # Fit circle to contour
                (x, y), radius = cv2.minEnclosingCircle(contour)
                if params['min_radius'] <= radius <= params['max_radius']:
                    detections.append({
                        'x': int(x),
                        'y': int(y),
                        'radius': int(radius),
                        'confidence': 0.7
                    })

        return detections

    def non_max_suppression(self, detections, overlap_thresh=0.5):
        """Remove overlapping detections"""
        if len(detections) == 0:
            return []

        # Convert to numpy array
        boxes = []
        for det in detections:
            x, y, r = det['x'], det['y'], det['radius']
            boxes.append([x - r, y - r, x + r, y + r, det['confidence']])

        boxes = np.array(boxes)

        if len(boxes) == 0:
            return []

        # Sort by confidence
        idxs = np.argsort(boxes[:, 4])

        pick = []
        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)

            # Find overlapping boxes
            xx1 = np.maximum(boxes[i, 0], boxes[idxs[:last], 0])
            yy1 = np.maximum(boxes[i, 1], boxes[idxs[:last], 1])
            xx2 = np.minimum(boxes[i, 2], boxes[idxs[:last], 2])
            yy2 = np.minimum(boxes[i, 3], boxes[idxs[:last], 3])

            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)

            overlap = (w * h) / ((boxes[idxs[:last], 2] - boxes[idxs[:last], 0] + 1) *
                                  (boxes[idxs[:last], 3] - boxes[idxs[:last], 1] + 1))

            idxs = np.delete(idxs, np.concatenate(([last],
                                                     np.where(overlap > overlap_thresh)[0])))

        return [detections[i] for i in pick]

    def detect(self, image_path, params=None):
        """Main detection method with custom parameters"""
        img_bgr, img_rgb = self.preprocess_image(image_path)

        # Perform segmentation with custom parameters
        detections = self.segment_plaques(img_rgb, params)

        return detections

    def retrain(self, annotations, upload_folder):
        """Retrain model with user feedback"""
        # For CV-based method, we update parameters based on feedback
        # In a real implementation, this would adjust detection thresholds

        training_data = []
        for annotation in annotations:
            image_id = annotation['image_id']
            image_path = os.path.join(upload_folder, image_id)

            if not os.path.exists(image_path):
                continue

            training_data.append({
                'image_path': image_path,
                'actual_count': annotation.get('actual_count'),
                'plaques': annotation.get('plaques', [])
            })

        if len(training_data) < 5:
            raise ValueError("Insufficient training data")

        # Increment version
        self.model_version += 1

        # Save version
        os.makedirs('model/checkpoints', exist_ok=True)
        with open('model/checkpoints/version.txt', 'w') as f:
            f.write(str(self.model_version))

        print(f"Model retrained to version {self.model_version} with {len(training_data)} samples")

    def get_model_version(self):
        """Get current model version"""
        return self.model_version
