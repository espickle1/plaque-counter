from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
from model.plaque_detector import PlaqueDetector
from utils.image_processor import ImageProcessor

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ANNOTATIONS_FOLDER = 'annotations'
MODEL_FOLDER = 'model/checkpoints'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ANNOTATIONS_FOLDER, exist_ok=True)
os.makedirs(MODEL_FOLDER, exist_ok=True)

# Initialize detector
detector = PlaqueDetector()
image_processor = ImageProcessor()


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Handle image upload and perform plaque detection"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save uploaded image
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # Process image and detect plaques
        detections = detector.detect(filepath)

        # Generate visualization
        viz_path = image_processor.create_visualization(
            filepath,
            detections,
            os.path.join(UPLOAD_FOLDER, f"viz_{filename}")
        )

        # Prepare response
        response = {
            'image_id': filename,
            'count': len(detections),
            'detections': detections,
            'visualization': f"/uploads/viz_{filename}",
            'original': f"/uploads/{filename}"
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Store user feedback for model improvement"""
    data = request.json

    if not data or 'image_id' not in data:
        return jsonify({'error': 'Invalid feedback data'}), 400

    # Save annotation data
    annotation_file = os.path.join(
        ANNOTATIONS_FOLDER,
        f"{data['image_id']}.json"
    )

    annotation_data = {
        'image_id': data['image_id'],
        'actual_count': data.get('actual_count'),
        'corrections': data.get('corrections', []),
        'timestamp': datetime.now().isoformat()
    }

    with open(annotation_file, 'w') as f:
        json.dump(annotation_data, f, indent=2)

    return jsonify({'message': 'Feedback saved successfully'})


@app.route('/api/retrain', methods=['POST'])
def retrain_model():
    """Trigger model retraining with accumulated feedback"""
    try:
        # Load all annotations
        annotations = []
        for filename in os.listdir(ANNOTATIONS_FOLDER):
            if filename.endswith('.json'):
                with open(os.path.join(ANNOTATIONS_FOLDER, filename), 'r') as f:
                    annotations.append(json.load(f))

        if len(annotations) < 5:
            return jsonify({
                'message': 'Need at least 5 annotated samples to retrain',
                'current_count': len(annotations)
            }), 400

        # Retrain model
        detector.retrain(annotations, UPLOAD_FOLDER)

        return jsonify({'message': f'Model retrained with {len(annotations)} samples'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about annotations and model"""
    annotation_count = len([f for f in os.listdir(ANNOTATIONS_FOLDER) if f.endswith('.json')])

    return jsonify({
        'annotation_count': annotation_count,
        'model_version': detector.get_model_version()
    })


@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
