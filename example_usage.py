#!/usr/bin/env python3
"""
Example script demonstrating programmatic usage of the plaque detector.

This script shows how to use the PlaqueDetector class directly without the web interface.
"""

import sys
from model.plaque_detector import PlaqueDetector
from utils.image_processor import ImageProcessor


def main():
    """Main function to demonstrate plaque detection"""

    if len(sys.argv) < 2:
        print("Usage: python example_usage.py <path_to_petri_dish_image>")
        print("\nExample:")
        print("  python example_usage.py sample_images/petri_dish_01.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    print(f"Analyzing image: {image_path}")
    print("-" * 50)

    # Initialize detector and processor
    detector = PlaqueDetector()
    processor = ImageProcessor()

    try:
        # Perform detection
        print("Detecting plaques...")
        detections = detector.detect(image_path)

        # Display results
        print(f"\nDetection Results:")
        print(f"  Total plaques detected: {len(detections)}")
        print(f"\nDetails:")

        for i, detection in enumerate(detections, 1):
            print(f"  Plaque #{i}:")
            print(f"    Position: ({detection['x']}, {detection['y']})")
            print(f"    Radius: {detection['radius']} pixels")
            print(f"    Confidence: {detection['confidence']:.2f}")

        # Create visualization
        output_path = image_path.replace('.', '_detected.')
        print(f"\nCreating visualization: {output_path}")
        processor.create_visualization(image_path, detections, output_path)

        print("\nAnalysis complete!")
        print(f"Visualization saved to: {output_path}")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
