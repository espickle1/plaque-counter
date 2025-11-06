// Global state
const state = {
    currentImage: null,
    imageData: null,
    plaques: [],
    autoDetectedPlaques: [],
    manualPlaques: [],
    imageId: null,
    annotationMode: 'add', // 'add' or 'remove'
    canvas: null,
    ctx: null,
    cameraStream: null,
    detectionParams: {
        minRadius: 5,
        maxRadius: 50,
        sensitivity: 30,
        minDistance: 20
    }
};

const API_BASE = 'http://localhost:5000/api';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadStats();
    loadHistory();
});

function initializeEventListeners() {
    // Camera and upload buttons
    document.getElementById('camera-btn').addEventListener('click', startCamera);
    document.getElementById('upload-btn').addEventListener('click', () => {
        document.getElementById('image-input').click();
    });
    document.getElementById('image-input').addEventListener('change', handleImageUpload);

    // Camera controls
    document.getElementById('capture-btn').addEventListener('click', capturePhoto);
    document.getElementById('cancel-camera-btn').addEventListener('click', stopCamera);

    // Analysis
    document.getElementById('analyze-btn').addEventListener('click', analyzeImage);

    // Canvas interaction
    state.canvas = document.getElementById('annotation-canvas');
    state.ctx = state.canvas.getContext('2d');
    state.canvas.addEventListener('click', handleCanvasClick);

    // Annotation mode buttons
    document.getElementById('mode-add').addEventListener('click', () => setAnnotationMode('add'));
    document.getElementById('mode-remove').addEventListener('click', () => setAnnotationMode('remove'));

    // Parameter controls
    ['min-radius', 'max-radius', 'sensitivity', 'min-distance'].forEach(id => {
        const input = document.getElementById(id);
        input.addEventListener('input', (e) => {
            const paramName = id.replace('-', '');
            const value = parseInt(e.target.value);
            state.detectionParams[paramName.replace('min', 'min').replace('max', 'max').replace('sensitivity', 'sensitivity').replace('distance', 'Distance')] = value;

            // Update display
            const key = id.replace(/-/g, '');
            if (key === 'minradius') state.detectionParams.minRadius = value;
            else if (key === 'maxradius') state.detectionParams.maxRadius = value;
            else if (key === 'sensitivity') state.detectionParams.sensitivity = value;
            else if (key === 'mindistance') state.detectionParams.minDistance = value;

            document.getElementById(id + '-value').textContent = value + (id.includes('radius') || id.includes('distance') ? 'px' : '');
        });
    });

    document.getElementById('redetect-btn').addEventListener('click', redetectWithParams);

    // Save controls
    document.getElementById('save-btn').addEventListener('click', saveResults);
    document.getElementById('download-btn').addEventListener('click', downloadImage);
    document.getElementById('new-image-btn').addEventListener('click', resetForNewImage);

    // Training
    document.getElementById('retrain-btn').addEventListener('click', retrainModel);
}

// === CAMERA FUNCTIONS ===
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
        });
        state.cameraStream = stream;

        const video = document.getElementById('camera-preview');
        video.srcObject = stream;

        document.getElementById('camera-container').style.display = 'block';
        document.getElementById('preview-container').style.display = 'none';

    } catch (error) {
        console.error('Camera error:', error);
        showToast('Could not access camera. Please check permissions.', 'error');
    }
}

function stopCamera() {
    if (state.cameraStream) {
        state.cameraStream.getTracks().forEach(track => track.stop());
        state.cameraStream = null;
    }
    document.getElementById('camera-container').style.display = 'none';
}

function capturePhoto() {
    const video = document.getElementById('camera-preview');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    canvas.toBlob(blob => {
        const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
        handleImageFile(file);
        stopCamera();
    }, 'image/jpeg', 0.95);
}

// === IMAGE UPLOAD FUNCTIONS ===
function handleImageUpload(e) {
    const file = e.target.files[0];
    if (file) {
        handleImageFile(file);
    }
}

function handleImageFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        state.currentImage = new Image();
        state.currentImage.onload = () => {
            displayImagePreview(e.target.result);
            state.imageData = file;
        };
        state.currentImage.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function displayImagePreview(src) {
    const preview = document.getElementById('image-preview');
    preview.src = src;
    document.getElementById('preview-container').style.display = 'block';
    document.getElementById('camera-container').style.display = 'none';
}

// === DETECTION FUNCTIONS ===
async function analyzeImage() {
    if (!state.imageData) {
        showToast('Please select an image first', 'error');
        return;
    }

    showLoading(true, 'Detecting plaques...');

    const formData = new FormData();
    formData.append('image', state.imageData);
    formData.append('min_radius', state.detectionParams.minRadius);
    formData.append('max_radius', state.detectionParams.maxRadius);
    formData.append('sensitivity', state.detectionParams.sensitivity);
    formData.append('min_distance', state.detectionParams.minDistance);

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Detection failed');

        const data = await response.json();
        state.imageId = data.image_id;
        state.autoDetectedPlaques = data.detections.map(d => ({...d, type: 'auto'}));
        state.plaques = [...state.autoDetectedPlaques];
        state.manualPlaques = [];

        setupAnnotationCanvas();
        showAnnotationSection();
        updateCounts();

        showToast(`Detected ${data.detections.length} plaques`, 'success');

    } catch (error) {
        console.error('Error:', error);
        showToast('Detection failed. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

async function redetectWithParams() {
    if (!state.imageData) return;

    showLoading(true, 'Re-detecting with new parameters...');

    const formData = new FormData();
    formData.append('image', state.imageData);
    formData.append('min_radius', state.detectionParams.minRadius);
    formData.append('max_radius', state.detectionParams.maxRadius);
    formData.append('sensitivity', state.detectionParams.sensitivity);
    formData.append('min_distance', state.detectionParams.minDistance);

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Re-detection failed');

        const data = await response.json();

        // Keep manual plaques, replace auto-detected ones
        state.autoDetectedPlaques = data.detections.map(d => ({...d, type: 'auto'}));
        state.plaques = [...state.autoDetectedPlaques, ...state.manualPlaques];

        redrawCanvas();
        updateCounts();

        showToast('Re-detection complete', 'success');

    } catch (error) {
        console.error('Error:', error);
        showToast('Re-detection failed', 'error');
    } finally {
        showLoading(false);
    }
}

// === CANVAS FUNCTIONS ===
function setupAnnotationCanvas() {
    const canvas = state.canvas;
    const img = state.currentImage;

    // Set canvas size to match image
    const maxWidth = 800;
    const scale = img.width > maxWidth ? maxWidth / img.width : 1;

    canvas.width = img.width * scale;
    canvas.height = img.height * scale;

    // Store scale for click coordinates
    state.canvasScale = scale;

    redrawCanvas();
}

function redrawCanvas() {
    const ctx = state.ctx;
    const canvas = state.canvas;
    const img = state.currentImage;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw image
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // Draw all plaques
    state.plaques.forEach((plaque, index) => {
        drawPlaque(plaque, index);
    });
}

function drawPlaque(plaque, index) {
    const ctx = state.ctx;
    const scale = state.canvasScale;

    const x = plaque.x * scale;
    const y = plaque.y * scale;
    const r = plaque.radius * scale;

    // Color based on type and confidence
    let color;
    if (plaque.type === 'manual') {
        color = '#00ff00'; // Green for manual
    } else if (plaque.confidence > 0.8) {
        color = '#00ff00'; // Lime
    } else if (plaque.confidence > 0.6) {
        color = '#ffff00'; // Yellow
    } else {
        color = '#ff0000'; // Red
    }

    // Draw circle
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.stroke();

    // Draw number
    ctx.fillStyle = color;
    ctx.font = 'bold 14px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Background for number
    const text = String(index + 1);
    const metrics = ctx.measureText(text);
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(x - metrics.width/2 - 4, y - 10, metrics.width + 8, 20);

    ctx.fillStyle = color;
    ctx.fillText(text, x, y);
}

function handleCanvasClick(e) {
    const rect = state.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / state.canvasScale;
    const y = (e.clientY - rect.top) / state.canvasScale;

    if (state.annotationMode === 'remove') {
        removePlaqueAt(x, y);
    } else {
        addPlaqueAt(x, y);
    }
}

function addPlaqueAt(x, y) {
    // Check if click is too close to existing plaque
    const minDistance = 15;
    const tooClose = state.plaques.some(p => {
        const dist = Math.sqrt((p.x - x) ** 2 + (p.y - y) ** 2);
        return dist < minDistance;
    });

    if (tooClose) {
        showToast('Too close to existing plaque', 'error');
        return;
    }

    const newPlaque = {
        x: Math.round(x),
        y: Math.round(y),
        radius: 15, // Default radius for manual plaques
        confidence: 1.0,
        type: 'manual'
    };

    state.plaques.push(newPlaque);
    state.manualPlaques.push(newPlaque);

    redrawCanvas();
    updateCounts();
    showToast('Plaque added', 'success');
}

function removePlaqueAt(x, y) {
    // Find plaque near click
    const clickRadius = 20;
    const index = state.plaques.findIndex(p => {
        const dist = Math.sqrt((p.x - x) ** 2 + (p.y - y) ** 2);
        return dist < clickRadius;
    });

    if (index !== -1) {
        const removed = state.plaques[index];
        state.plaques.splice(index, 1);

        // Also remove from appropriate list
        if (removed.type === 'manual') {
            const manualIndex = state.manualPlaques.findIndex(p => p.x === removed.x && p.y === removed.y);
            if (manualIndex !== -1) state.manualPlaques.splice(manualIndex, 1);
        } else {
            const autoIndex = state.autoDetectedPlaques.findIndex(p => p.x === removed.x && p.y === removed.y);
            if (autoIndex !== -1) state.autoDetectedPlaques.splice(autoIndex, 1);
        }

        redrawCanvas();
        updateCounts();
        showToast('Plaque removed', 'success');
    } else {
        showToast('No plaque found at click location', 'error');
    }
}

function setAnnotationMode(mode) {
    state.annotationMode = mode;

    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.querySelector(`[data-mode="${mode}"]`).classList.add('active');

    // Change cursor
    state.canvas.style.cursor = mode === 'add' ? 'crosshair' : 'not-allowed';
}

// === UI UPDATE FUNCTIONS ===
function showAnnotationSection() {
    document.getElementById('annotation-section').style.display = 'block';
    document.getElementById('save-section').style.display = 'block';

    // Update preview canvas
    updatePreviewCanvas();

    // Scroll to annotation section
    document.getElementById('annotation-section').scrollIntoView({ behavior: 'smooth' });
}

function updateCounts() {
    const autoCount = state.autoDetectedPlaques.length;
    const manualCount = state.manualPlaques.length;
    const totalCount = state.plaques.length;

    document.getElementById('auto-count').textContent = autoCount;
    document.getElementById('manual-count').textContent = manualCount;
    document.getElementById('total-count').textContent = totalCount;
    document.getElementById('current-count').textContent = totalCount;

    // Update save section
    document.getElementById('final-count').textContent = totalCount;
    document.getElementById('final-auto').textContent = autoCount;
    document.getElementById('final-manual').textContent = manualCount;

    updatePreviewCanvas();
}

function updatePreviewCanvas() {
    const previewCanvas = document.getElementById('preview-canvas');
    const ctx = previewCanvas.getContext('2d');

    if (!state.currentImage) return;

    // Same size as annotation canvas
    previewCanvas.width = state.canvas.width;
    previewCanvas.height = state.canvas.height;

    // Copy from annotation canvas
    ctx.drawImage(state.canvas, 0, 0);
}

// === SAVE FUNCTIONS ===
async function saveResults() {
    const sampleName = document.getElementById('sample-name').value || 'Untitled';
    const notes = document.getElementById('notes').value;
    const saveImage = document.getElementById('save-image').checked;
    const saveData = document.getElementById('save-data').checked;

    showLoading(true, 'Saving results...');

    try {
        // Prepare annotation data
        const annotationData = {
            image_id: state.imageId,
            sample_name: sampleName,
            notes: notes,
            total_count: state.plaques.length,
            auto_detected_count: state.autoDetectedPlaques.length,
            manual_count: state.manualPlaques.length,
            plaques: state.plaques,
            detection_params: state.detectionParams,
            timestamp: new Date().toISOString()
        };

        // Save to backend
        const response = await fetch(`${API_BASE}/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(annotationData)
        });

        if (!response.ok) throw new Error('Save failed');

        // Download image if requested
        if (saveImage) {
            downloadImage();
        }

        showToast('Results saved successfully!', 'success');
        loadStats();
        loadHistory();

    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to save results', 'error');
    } finally {
        showLoading(false);
    }
}

function downloadImage() {
    const canvas = state.canvas;
    canvas.toBlob(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `plaque-count-${Date.now()}.png`;
        a.click();
        URL.revokeObjectURL(url);
    });
}

function resetForNewImage() {
    // Reset state
    state.currentImage = null;
    state.imageData = null;
    state.plaques = [];
    state.autoDetectedPlaques = [];
    state.manualPlaques = [];
    state.imageId = null;

    // Reset UI
    document.getElementById('preview-container').style.display = 'none';
    document.getElementById('annotation-section').style.display = 'none';
    document.getElementById('save-section').style.display = 'none';
    document.getElementById('sample-name').value = '';
    document.getElementById('notes').value = '';

    updateCounts();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// === STATS AND HISTORY ===
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        if (!response.ok) return;

        const data = await response.json();
        document.getElementById('annotation-count').textContent = data.annotation_count || 0;
        document.getElementById('model-version').textContent = data.model_version || 0;
        document.getElementById('train-count').textContent = data.annotation_count || 0;

        const retrainBtn = document.getElementById('retrain-btn');
        retrainBtn.disabled = (data.annotation_count || 0) < 5;

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/history`);
        if (!response.ok) return;

        const data = await response.json();
        const historyDiv = document.getElementById('results-history');

        if (data.length === 0) {
            historyDiv.innerHTML = '<p class="no-history">No saved results yet.</p>';
            return;
        }

        historyDiv.innerHTML = data.map(item => `
            <div class="history-item">
                <h4>${item.sample_name || 'Untitled'}</h4>
                <p><strong>Count:</strong> ${item.total_count} plaques</p>
                <p><strong>Date:</strong> ${new Date(item.timestamp).toLocaleString()}</p>
                ${item.notes ? `<p><strong>Notes:</strong> ${item.notes}</p>` : ''}
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading history:', error);
    }
}

async function retrainModel() {
    if (!confirm('Train model with all saved annotations? This may take a few minutes.')) {
        return;
    }

    showLoading(true, 'Training model...');

    try {
        const response = await fetch(`${API_BASE}/retrain`, { method: 'POST' });
        if (!response.ok) throw new Error('Training failed');

        const data = await response.json();
        showToast(data.message, 'success');
        loadStats();

    } catch (error) {
        console.error('Error:', error);
        showToast('Training failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// === UTILITY FUNCTIONS ===
function showLoading(show, message = 'Processing...') {
    const overlay = document.getElementById('loading-overlay');
    const text = document.getElementById('loading-text');

    if (show) {
        overlay.classList.add('active');
        text.textContent = message;
    } else {
        overlay.classList.remove('active');
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
