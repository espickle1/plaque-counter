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
SAVED_RESULTS_FOLDER = 'saved_results'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ANNOTATIONS_FOLDER, exist_ok=True)
os.makedirs(MODEL_FOLDER, exist_ok=True)
os.makedirs(SAVED_RESULTS_FOLDER, exist_ok=True)

# Initialize detector
detector = PlaqueDetector()
image_processor = ImageProcessor()


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Handle image upload and perform plaque detection with custom parameters"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Get detection parameters from request
    params = {
        'min_radius': int(request.form.get('min_radius', 5)),
        'max_radius': int(request.form.get('max_radius', 50)),
        'sensitivity': int(request.form.get('sensitivity', 30)),
        'min_distance': int(request.form.get('min_distance', 20))
    }

    # Save uploaded image
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # Process image and detect plaques with custom parameters
        detections = detector.detect(filepath, params)

        # Prepare response
        response = {
            'image_id': filename,
            'count': len(detections),
            'detections': detections,
            'original': f"/uploads/{filename}",
            'params': params
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/save', methods=['POST'])
def save_results():
    """Save annotated results with user corrections"""
    data = request.json

    if not data or 'image_id' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        # Create unique ID for this result
        result_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

        # Save annotation data
        annotation_file = os.path.join(
            SAVED_RESULTS_FOLDER,
            f"{result_id}.json"
        )

        result_data = {
            'id': result_id,
            'image_id': data.get('image_id'),
            'sample_name': data.get('sample_name', 'Untitled'),
            'notes': data.get('notes', ''),
            'total_count': data.get('total_count', 0),
            'auto_detected_count': data.get('auto_detected_count', 0),
            'manual_count': data.get('manual_count', 0),
            'plaques': data.get('plaques', []),
            'detection_params': data.get('detection_params', {}),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }

        with open(annotation_file, 'w') as f:
            json.dump(result_data, f, indent=2)

        # Also save to annotations folder for training
        training_annotation_file = os.path.join(
            ANNOTATIONS_FOLDER,
            f"{data['image_id']}.json"
        )

        training_data = {
            'image_id': data['image_id'],
            'actual_count': data['total_count'],
            'plaques': data.get('plaques', []),
            'timestamp': result_data['timestamp']
        }

        with open(training_annotation_file, 'w') as f:
            json.dump(training_data, f, indent=2)

        return jsonify({
            'message': 'Results saved successfully',
            'result_id': result_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get all saved results"""
    try:
        results = []

        for filename in os.listdir(SAVED_RESULTS_FOLDER):
            if filename.endswith('.json'):
                filepath = os.path.join(SAVED_RESULTS_FOLDER, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    results.append(data)

        # Sort by timestamp, newest first
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Store user feedback for model improvement (legacy endpoint)"""
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
    saved_results_count = len([f for f in os.listdir(SAVED_RESULTS_FOLDER) if f.endswith('.json')])
    annotation_count = len([f for f in os.listdir(ANNOTATIONS_FOLDER) if f.endswith('.json')])

    return jsonify({
        'annotation_count': annotation_count,
        'saved_results_count': saved_results_count,
        'model_version': detector.get_model_version()
    })


@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
