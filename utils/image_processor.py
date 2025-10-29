import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import os


class ImageProcessor:
    """Utility class for image processing and visualization"""

    def create_visualization(self, image_path, detections, output_path):
        """
        Create visualization with detected plaques highlighted

        Args:
            image_path: Path to original image
            detections: List of detection dictionaries
            output_path: Path to save visualization

        Returns:
            Path to saved visualization
        """
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Create visualization
        fig, ax = plt.subplots(1, figsize=(12, 12))
        ax.imshow(img_rgb)
        ax.axis('off')

        # Draw circles for each detection
        for i, detection in enumerate(detections):
            x = detection['x']
            y = detection['y']
            r = detection['radius']
            confidence = detection.get('confidence', 1.0)

            # Color based on confidence (green = high, yellow = medium, red = low)
            if confidence > 0.8:
                color = 'lime'
            elif confidence > 0.6:
                color = 'yellow'
            else:
                color = 'red'

            # Draw circle
            circle = Circle((x, y), r, fill=False, edgecolor=color,
                            linewidth=2, alpha=0.8)
            ax.add_patch(circle)

            # Add label with number
            ax.text(x, y, str(i + 1), color='white',
                    fontsize=10, ha='center', va='center',
                    bbox=dict(boxstyle='round', facecolor=color, alpha=0.7))

        # Add title with count
        ax.set_title(f'Detected Plaques: {len(detections)}',
                     fontsize=16, fontweight='bold', pad=20)

        # Save figure
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        return output_path

    def apply_mask(self, image, mask):
        """Apply binary mask to image"""
        return cv2.bitwise_and(image, image, mask=mask)

    def enhance_contrast(self, image):
        """Enhance image contrast using CLAHE"""
        if len(image.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)

            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)

            # Merge channels
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        else:
            # Grayscale image
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)

        return enhanced

    def preprocess_for_detection(self, image_path):
        """
        Preprocess image to enhance plaque visibility

        Returns:
            Preprocessed image array
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Enhance contrast
        enhanced = self.enhance_contrast(img_rgb)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

        return blurred

    def crop_region(self, image, x, y, size):
        """Crop a region from image centered at (x, y)"""
        h, w = image.shape[:2]
        half_size = size // 2

        x1 = max(0, x - half_size)
        y1 = max(0, y - half_size)
        x2 = min(w, x + half_size)
        y2 = min(h, y + half_size)

        return image[y1:y2, x1:x2]
