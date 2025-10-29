// Global state
let currentImageId = null;
let currentDetections = [];
let selectedAccuracy = null;

// API base URL
const API_BASE = 'http://localhost:5000/api';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadStats();
});

function initializeEventListeners() {
    // Upload area
    const uploadArea = document.getElementById('upload-area');
    const imageInput = document.getElementById('image-input');

    uploadArea.addEventListener('click', () => imageInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleImageSelect(file);
        }
    });

    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleImageSelect(file);
        }
    });

    // Analyze button
    document.getElementById('analyze-btn').addEventListener('click', analyzeImage);

    // Feedback buttons
    const feedbackBtns = document.querySelectorAll('.feedback-btn');
    feedbackBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            feedbackBtns.forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            selectedAccuracy = btn.dataset.accuracy;
        });
    });

    // Submit feedback
    document.getElementById('submit-feedback-btn').addEventListener('click', submitFeedback);

    // Retrain button
    document.getElementById('retrain-btn').addEventListener('click', retrainModel);
}

function handleImageSelect(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        // Preview image in upload area
        const uploadArea = document.getElementById('upload-area');
        uploadArea.innerHTML = `
            <img src="${e.target.result}" style="max-width: 100%; max-height: 300px; border-radius: 8px;">
            <p style="margin-top: 15px;">Image ready to analyze</p>
        `;
        document.getElementById('analyze-btn').disabled = false;

        // Store file for upload
        window.currentFile = file;
    };
    reader.readAsDataURL(file);
}

async function analyzeImage() {
    if (!window.currentFile) {
        showToast('Please select an image first', 'error');
        return;
    }

    showLoading(true);

    const formData = new FormData();
    formData.append('image', window.currentFile);

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();
        displayResults(data);
        showToast('Analysis complete!', 'success');

    } catch (error) {
        console.error('Error:', error);
        showToast('Analysis failed. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

function displayResults(data) {
    currentImageId = data.image_id;
    currentDetections = data.detections;

    // Show results section
    document.getElementById('results-section').style.display = 'block';
    document.getElementById('feedback-section').style.display = 'block';

    // Display images
    document.getElementById('original-image').src = data.original;
    document.getElementById('detected-image').src = data.visualization;

    // Display count
    document.getElementById('plaque-count').textContent = data.count;

    // Scroll to results
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

async function submitFeedback() {
    const actualCount = document.getElementById('actual-count').value;
    const notes = document.getElementById('notes').value;

    if (!actualCount) {
        showToast('Please enter the actual plaque count', 'error');
        return;
    }

    if (!selectedAccuracy) {
        showToast('Please rate the detection accuracy', 'error');
        return;
    }

    const feedbackData = {
        image_id: currentImageId,
        actual_count: parseInt(actualCount),
        detected_count: currentDetections.length,
        accuracy: selectedAccuracy,
        notes: notes,
        corrections: []
    };

    try {
        const response = await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(feedbackData)
        });

        if (!response.ok) {
            throw new Error('Feedback submission failed');
        }

        showToast('Feedback submitted successfully!', 'success');

        // Reset form
        document.getElementById('actual-count').value = '';
        document.getElementById('notes').value = '';
        document.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.classList.remove('selected');
        });
        selectedAccuracy = null;

        // Reload stats
        loadStats();

    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to submit feedback', 'error');
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        if (!response.ok) {
            throw new Error('Failed to load stats');
        }

        const data = await response.json();
        document.getElementById('annotation-count').textContent = data.annotation_count;
        document.getElementById('model-version').textContent = data.model_version;

        // Enable retrain button if enough annotations
        const retrainBtn = document.getElementById('retrain-btn');
        if (data.annotation_count >= 5) {
            retrainBtn.disabled = false;
            retrainBtn.parentElement.querySelector('p').textContent =
                `${data.annotation_count} samples available. Ready to retrain!`;
        }

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function retrainModel() {
    if (!confirm('This will retrain the model with all collected feedback. Continue?')) {
        return;
    }

    showLoading(true, 'Training model...');

    try {
        const response = await fetch(`${API_BASE}/retrain`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Retraining failed');
        }

        const data = await response.json();
        showToast(data.message, 'success');
        loadStats();

    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function showLoading(show, message = 'Processing image...') {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.add('active');
        overlay.querySelector('p').textContent = message;
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
