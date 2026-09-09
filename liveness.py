"""
ml_models/liveness.py

This module handles Test 1 (Document Anti-Spoofing via FFT) and 
Test 2 (Human Liveness / Presentation Attack Detection).
"""
import cv2
import numpy as np
from core.schemas import TestStatus

# ==========================================
# TEST 1: DOCUMENT ANTI-SPOOFING (Moire Detection)
# ==========================================

def detect_moire_pattern(image: np.ndarray, threshold: float = 0.85) -> TestStatus:
    """
    Test 1: Detects if the document is a physical card or a picture of a digital screen.
    Digital screens (OLED/LCD) emit a microscopic pixel grid. When captured by a webcam,
    it creates a high-frequency interference pattern known as a Moire pattern.
    We use a 2D Fast Fourier Transform (FFT) to find these unnatural frequencies.
    """
    try:
        # Convert the image to grayscale for structural analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate the 2D Fast Fourier Transform (FFT)
        # This converts the image from the "spatial domain" (pixels) 
        # into the "frequency domain" (waves).
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        
        # Calculate the magnitude spectrum
        magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1)
        
        # Find the center of the frequency map (low frequencies / flat colors)
        rows, cols = gray.shape
        crow, ccol = rows // 2, cols // 2
        
        # Mask out the center (low frequencies) to isolate the high frequencies.
        # Moire patterns live in the extreme high-frequency bands.
        r = 30  # radius of the low-frequency mask
        magnitude_spectrum[crow-r:crow+r, ccol-r:ccol+r] = 0
        
        # Calculate the ratio of high-frequency energy
        # If the image is a physical card, this energy is low.
        # If it is a digital screen, the pixel grid causes a massive energy spike.
        high_freq_ratio = np.sum(magnitude_spectrum > 200) / (rows * cols)
        
        # If the high-frequency anomalies exceed our threshold, it's a screen replay attack
        if high_freq_ratio > threshold:
            return TestStatus.FAIL # Screen detected
            
        return TestStatus.PASS # Physical paper/plastic verified
        
    except Exception as e:
        print(f"Moire detection error: {e}")
        return TestStatus.ALERT


# ==========================================
# TEST 2: HUMAN ANTI-SPOOFING (Passive Liveness)
# ==========================================

def verify_human_liveness(selfie_img: np.ndarray) -> TestStatus:
    """
    Test 2: Detects if the selfie is a real, live human or a printed photograph/mask.
    
    For a hackathon, building a full 3D depth-map CNN from scratch is too slow.
    Instead, we simulate the architecture of a PAD (Presentation Attack Detection) model 
    by analyzing the localized texture and glare of the face.
    
    In a production environment, you would swap this function's internals with 
    a lightweight pretrained model like MiniFASNet (Silent-Face-Anti-Spoofing).
    """
    try:
        # Step 1: Detect the face and crop tightly (simulated here)
        gray = cv2.cvtColor(selfie_img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            # If no face is found in the selfie, liveness automatically fails
            return TestStatus.FAIL
            
        x, y, w, h = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        
        # Step 2: Texture Analysis (Laplacian Variance)
        # Printed photos held up to a webcam lose their micro-textures and depth sharpness.
        # We use the variance of the Laplacian to measure the structural focus of the face.
        laplacian_var = cv2.Laplacian(face_roi, cv2.CV_64F).var()
        
        # A real 3D face will have varying depth (nose is sharp, ears might be slightly blurred).
        # A flat 2D printed photo will have a uniformly flat blur variance.
        # Note: 50 is an arbitrary threshold for the hackathon demo.
        if laplacian_var < 50.0:
            return TestStatus.FAIL # Flat 2D texture detected (Spoof)
            
        return TestStatus.PASS # 3D human texture verified
        
    except Exception as e:
        print(f"Liveness engine error: {e}")
        return TestStatus.ALERT
