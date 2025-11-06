# Quick Start Guide

## Installation

### Step 1: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Note**: If you get permission errors, try:
```bash
pip install --user -r requirements.txt
```

Or use a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Start the Server

```bash
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

### Step 3: Open in Browser

Open your web browser and go to:
```
http://localhost:5000
```

## Troubleshooting

### "No module named 'flask'" error
**Solution**: Run `pip install -r requirements.txt`

### "No module named 'cv2'" error
**Solution**: Run `pip install opencv-python`

### Upload button not working
**Make sure**:
1. The server is running (`python app.py`)
2. You're accessing `http://localhost:5000` (not opening the HTML file directly)
3. Check browser console (F12) for JavaScript errors

### Camera not working
- Make sure you're using HTTPS or localhost
- Grant camera permissions when prompted
- Try uploading an image instead if camera fails

## Testing the Application

1. **Upload a test image** - Any image with circular objects
2. **Click "Detect Plaques"** - Should show detected circles
3. **Try clicking on the image** - Should add/remove plaques
4. **Adjust parameters** - Sliders should update detection
5. **Save results** - Check the history section

## Need Help?

The application works entirely in your browser with a Python backend:
- Frontend: HTML/CSS/JavaScript (interactive canvas)
- Backend: Flask API (Python)
- Detection: OpenCV computer vision algorithms

Make sure both are running for full functionality!
