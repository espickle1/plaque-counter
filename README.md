# Phage Plaque Counter

An AI-powered web application for automated detection and counting of bacteriophage plaques in petri dish images. This tool combines computer vision and deep learning to quantify phage killing efficiency with continuous model improvement through user feedback.

## Features

- **Automated Plaque Detection**: Deep learning-based detection using computer vision algorithms
- **Interactive Web Interface**: User-friendly interface for image upload and analysis
- **Visual Results**: Highlighted visualization of detected plaques with confidence scores
- **User Feedback Loop**: Collect corrections and annotations to improve model accuracy
- **Model Retraining**: Automated retraining pipeline with accumulated user feedback
- **Real-time Statistics**: Track annotations and model versions

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

### 1. Upload Image

- Click the upload area or drag and drop a petri dish image
- Supported formats: JPG, PNG
- Recommended: Clear, well-lit images with visible plaques

### 2. Analyze

- Click "Analyze Image" to start detection
- The system will process the image and detect plaques
- Results show:
  - Original image
  - Visualization with highlighted plaques
  - Total plaque count

### 3. Provide Feedback

- Enter the actual number of plaques you observe
- Rate the detection accuracy (Excellent/Good/Fair/Poor)
- Add notes about any issues or observations
- Submit feedback to improve the model

### 4. Retrain Model

- After collecting at least 5 annotated samples
- Click "Retrain Model" to update the detection algorithm
- The model will incorporate your corrections for better accuracy

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
├── model/
│   ├── __init__.py
│   ├── plaque_detector.py     # Main detection class
│   └── checkpoints/           # Model weights
├── utils/
│   ├── __init__.py
│   └── image_processor.py     # Image processing utilities
├── static/
│   ├── index.html             # Web interface
│   ├── style.css              # Styling
│   └── app.js                 # Frontend logic
├── uploads/                   # Uploaded images (created at runtime)
└── annotations/               # User feedback data (created at runtime)
```

## API Endpoints

### POST /api/upload
Upload and analyze a petri dish image.

**Request**: multipart/form-data with 'image' field
**Response**: JSON with detections and visualization paths

### POST /api/feedback
Submit user feedback for an analyzed image.

**Request**: JSON with image_id, actual_count, accuracy, notes
**Response**: Success confirmation

### POST /api/retrain
Trigger model retraining with accumulated feedback.

**Request**: Empty POST
**Response**: Training status and message

### GET /api/stats
Get current statistics about annotations and model version.

**Response**: JSON with annotation_count and model_version

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

## Future Enhancements

- [ ] Integration with Detectron2 for instance segmentation
- [ ] Interactive plaque annotation tool with click-to-mark interface
- [ ] Batch processing for multiple images
- [ ] Export results to CSV/Excel
- [ ] Advanced metrics (plaque size distribution, clarity scores)
- [ ] Integration with laboratory information systems
- [ ] Multi-user support with authentication
- [ ] Cloud deployment options

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
