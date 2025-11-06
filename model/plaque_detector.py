import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
import numpy as np
from skimage import measure, morphology
from scipy import ndimage
import os
import json


class PlaqueDetectionModel(nn.Module):
    """CNN model for plaque feature extraction and classification"""

    def __init__(self):
        super(PlaqueDetectionModel, self).__init__()
        # Use ResNet18 as backbone
        resnet = models.resnet18(pretrained=True)
        # Remove final FC layer
        self.features = nn.Sequential(*list(resnet.children())[:-2])

        # Add custom layers for plaque detection
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 2)  # plaque vs background
        )

    def forward(self, x):
        features = self.features(x)
        output = self.classifier(features)
        return output


class PlaqueDetector:
    """Main plaque detection class combining traditional CV and deep learning"""

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = PlaqueDetectionModel().to(self.device)
        self.model_version = 0

        # Load checkpoint if exists
        checkpoint_path = 'model/checkpoints/latest.pth'
        if os.path.exists(checkpoint_path):
            self.load_model(checkpoint_path)

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

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

        # TODO: Add deep learning refinement for classification
        # For now, using traditional CV methods

        return detections

    def retrain(self, annotations, upload_folder):
        """Retrain model with user feedback"""
        # Prepare training data from annotations
        training_data = []

        for annotation in annotations:
            image_id = annotation['image_id']
            image_path = os.path.join(upload_folder, image_id)

            if not os.path.exists(image_path):
                continue

            corrections = annotation.get('corrections', [])
            actual_count = annotation.get('actual_count')

            training_data.append({
                'image_path': image_path,
                'corrections': corrections,
                'actual_count': actual_count
            })

        if len(training_data) < 5:
            raise ValueError("Insufficient training data")

        # TODO: Implement training loop
        # For now, just increment version
        self.model_version += 1
        self.save_model(f'model/checkpoints/version_{self.model_version}.pth')

        print(f"Model retrained to version {self.model_version} with {len(training_data)} samples")

    def save_model(self, path):
        """Save model checkpoint"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'version': self.model_version
        }, path)

        # Also save as latest
        latest_path = 'model/checkpoints/latest.pth'
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'version': self.model_version
        }, latest_path)

    def load_model(self, path):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model_version = checkpoint.get('version', 0)
        print(f"Loaded model version {self.model_version}")

    def get_model_version(self):
        """Get current model version"""
        return self.model_version
