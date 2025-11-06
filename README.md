# Phage Plaque Counter v2.0

An AI-powered web application for automated detection and counting of bacteriophage plaques in petri dish images. Features **interactive annotation**, **camera capture**, and **adjustable detection parameters** for accurate plaque counting with continuous model improvement.

## Key Features

- **📸 Camera Capture**: Take photos directly with your device camera or upload images
- **🎯 Interactive Annotation**: Click to add or remove plaques directly on the image
- **⚙️ Adjustable Parameters**: Fine-tune detection sensitivity, size limits, and spacing
- **🖼️ Real-time Visualization**: See detected plaques highlighted with confidence colors
- **💾 Save & Export**: Download annotated images and save counting data
- **📊 Results History**: Track all your saved counts with notes and timestamps
- **🧠 Continuous Learning**: Model improves automatically from your corrections
- **📱 Mobile-Friendly**: Responsive design works on phones, tablets, and desktops

## Background

Bacteriophages (phages) kill bacteria by creating clearings called "plaques" in a bacterial lawn on petri dishes. Each plaque originates from a single phage that infected bacteria and multiplied. By counting plaques, researchers can:
- Quantify the number of phages in a sample
- Measure the efficiency of bacterial killing
- Conduct phage therapy research

## Technology Stack

- **Backend**: Flask (Python)
- **Deep Learning**: PyTorch with ResNet18 backbone
- **Computer Vision**: OpenCV, scikit-image
- **Frontend**: HTML5, CSS3, JavaScript
- **Image Processing**: Hough Circle Transform, Adaptive Thresholding

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- At least 4GB RAM
- Modern web browser (Chrome, Firefox, Safari)

### Setup Instructions

1. **Clone or navigate to the repository**:
   ```bash
   cd plaque-counter
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

## Usage Guide

### Step 1: Capture or Upload Image

**Option A: Camera Capture**
1. Click "Take Photo" button
2. Allow camera access when prompted
3. Frame your petri dish in the camera view
4. Click "Capture Photo" to take the picture

**Option B: Upload Image**
1. Click "Upload Image" button
2. Select a petri dish image from your device
3. Supported formats: JPG, PNG
4. Click "Detect Plaques" to start analysis

### Step 2: Review and Correct Detections

The system automatically detects plaques, but you can refine the results:

**Add Missed Plaques:**
1. Ensure "Add Plaque" mode is selected (green button)
2. Click anywhere on the image to mark a missed plaque
3. Count updates automatically

**Remove False Detections:**
1. Click "Remove Plaque" mode button
2. Click on an incorrect detection to remove it
3. Count updates in real-time

**Adjust Detection Parameters:**
- **Minimum Size**: Smallest plaque radius to detect
- **Maximum Size**: Largest plaque radius to detect
- **Sensitivity**: Lower = stricter matching, Higher = more permissive
- **Minimum Distance**: Minimum spacing between plaques
- Click "Re-detect with Parameters" to run detection again

**Visual Feedback:**
- Green circles = High confidence detections or manual additions
- Yellow circles = Medium confidence
- Red circles = Low confidence
- Each plaque is numbered for easy reference

### Step 3: Save Results

1. **Add Sample Information** (optional):
   - Enter a sample name (e.g., "Experiment-A-Plate-1")
   - Add notes about the sample

2. **Choose Save Options**:
   - ✓ Save annotated image - Saves the image with circles and numbers
   - ✓ Save count data - Saves the plaque count and metadata

3. **Actions**:
   - **Save Results**: Saves to database and history
   - **Download Image**: Downloads annotated image to your device
   - **Analyze New Image**: Start over with a new sample

### Step 4: View History & Train Model

**View Saved Results:**
- Scroll to "Saved Results" section
- See all your previous counts with dates and notes

**Train the Model:**
- Save at least 5 annotated samples
- Click "Train Model" button
- The model learns from your corrections
- Future detections become more accurate

## How It Works

### Detection Pipeline

1. **Image Preprocessing**:
   - Convert to grayscale
   - Apply Gaussian blur to reduce noise
   - Enhance contrast using CLAHE

2. **Plaque Segmentation**:
   - **Hough Circle Transform**: Detects circular plaques
   - **Adaptive Thresholding**: Finds irregular plaques
   - Non-maximum suppression to remove overlaps

3. **Deep Learning Classification** (in development):
   - ResNet18 backbone for feature extraction
   - Custom classifier for plaque vs. background
   - Continuous learning from user feedback

4. **Visualization**:
   - Draw circles around detected plaques
   - Color-code by confidence (green=high, yellow=medium, red=low)
   - Number each detection

### Model Training

The system uses an iterative training approach:

1. **Initial Model**: Pre-trained ResNet18 with transfer learning
2. **User Corrections**: Collect actual counts and feedback
3. **Annotation Storage**: Save corrections in JSON format
4. **Retraining**: Update model with new training data
5. **Validation**: Improve detection accuracy over time

## Project Structure

```
plaque-counter/
├── app.py                      # Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── example_usage.py            # Command-line usage example
├── model/
│   ├── __init__.py
│   ├── plaque_detector.py     # Main detection class
│   └── checkpoints/           # Model weights (created at runtime)
├── utils/
│   ├── __init__.py
│   └── image_processor.py     # Image processing utilities
├── static/
│   ├── index.html             # Web interface
│   ├── style.css              # Styling
│   └── app.js                 # Frontend logic (interactive annotation)
├── uploads/                   # Uploaded images (created at runtime)
├── annotations/               # Training annotations (created at runtime)
└── saved_results/             # Saved counting results (created at runtime)
```

## API Endpoints

### POST /api/upload
Upload and analyze a petri dish image with custom parameters.

**Request**:
- `multipart/form-data` with 'image' field
- Optional: min_radius, max_radius, sensitivity, min_distance

**Response**: JSON with detections, count, image_id, and parameters

### POST /api/save
Save annotated results with user corrections.

**Request**: JSON with:
- image_id
- sample_name (optional)
- notes (optional)
- total_count
- auto_detected_count
- manual_count
- plaques (array of plaque objects)
- detection_params

**Response**: Success confirmation with result_id

### GET /api/history
Get all saved counting results.

**Response**: JSON array of all saved results sorted by timestamp

### POST /api/retrain
Trigger model retraining with accumulated annotations.

**Request**: Empty POST
**Response**: Training status and message (requires 5+ annotations)

### GET /api/stats
Get statistics about saved results and model version.

**Response**: JSON with:
- annotation_count
- saved_results_count
- model_version

## Tips for Best Results

1. **Image Quality**:
   - Use well-lit, in-focus images
   - Ensure the entire petri dish is visible
   - Avoid glare or reflections
   - Higher resolution is better (minimum 800x800px)

2. **Providing Feedback**:
   - Be accurate with actual counts
   - Note any systematic errors (e.g., consistently missed small plaques)
   - Provide feedback on diverse images (different lighting, plaque sizes)

3. **Model Training**:
   - Collect at least 10-20 samples before retraining for best results
   - Include variety in your training set
   - Retrain periodically as you collect more data

## Troubleshooting

### "Could not load image" error
- Ensure the image file is not corrupted
- Try converting to JPG or PNG format
- Check file permissions

### Detection missing plaques
- Provide feedback with actual count
- Accumulate more training samples
- Consider image quality improvements

### Model retraining fails
- Ensure at least 5 annotated samples
- Check that annotation files exist in annotations/ folder
- Review server logs for errors

## What's New in v2.0

✅ **Interactive Annotation** - Click to add/remove plaques directly on images
✅ **Camera Capture** - Take photos with your device camera
✅ **Adjustable Parameters** - Real-time control over detection settings
✅ **Results History** - Track all your saved counts and annotations
✅ **Download Capability** - Export annotated images instantly
✅ **Mobile Support** - Fully responsive design for phones and tablets
✅ **Real-time Updates** - See count changes immediately as you annotate

## Future Enhancements

- [ ] Integration with Detectron2 for instance segmentation
- [ ] Batch processing for multiple images
- [ ] Export results to CSV/Excel
- [ ] Advanced metrics (plaque size distribution, clarity scores)
- [ ] Integration with laboratory information systems
- [ ] Multi-user support with authentication
- [ ] Cloud deployment options
- [ ] Undo/redo for annotations
- [ ] Keyboard shortcuts for faster annotation

## Contributing

Contributions are welcome! Areas for improvement:
- Enhanced detection algorithms
- Better visualization options
- Additional export formats
- Performance optimizations
- Documentation improvements

## License

This project is for research and educational purposes.

## Citation

If you use this tool in your research, please acknowledge:
```
Phage Plaque Counter - AI-powered bacteriophage plaque detection system
```

## Support

For issues, questions, or suggestions, please open an issue in the repository or contact the development team.

## Acknowledgments

- Built with PyTorch and Flask
- Uses OpenCV for image processing
- Inspired by the need for automated phage quantification in research labs
