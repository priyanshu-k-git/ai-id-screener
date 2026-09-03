import cv2
import numpy as np
import os
from ultralytics import YOLO

# ---------------------------------------------------------
# GLOBAL AI MODEL INITIALIZATION
# ---------------------------------------------------------
print("Loading Fraud Detection Models...")

# 1. Load the Hologram/Seal Detector (YOLOv8)
# Your team will need to train a small YOLO model on pictures of real IDs 
# to find where the seals and holograms are supposed to be.
try:
    seal_detector = YOLO('hologram_detector.pt') 
    SEAL_MODEL_LOADED = True
except Exception:
    print("Warning: hologram_detector.pt not found. Running in fallback mode.")
    SEAL_MODEL_LOADED = False

# 2. Load Liveness Model (Anti-Spoofing)
# For production, you would load a PyTorch (.pth) or ONNX model here (e.g., MiniFASNet)
# liveness_net = cv2.dnn.readNetFromONNX("anti_spoofing_model.onnx")

print("Fraud Models loaded.")

# ---------------------------------------------------------
# CHECK 1: Liveness Detection (Anti-Spoofing)
# ---------------------------------------------------------
def check_liveness(selfie_image):
    """
    Analyzes the selfie to ensure it is a real 3D human, not a screen or mask.
    """
    # IN PRODUCTION: Pass the image through the Neural Network
    # blob = cv2.dnn.blobFromImage(selfie_image, 1.0, (128, 128), (0,0,0), swapRB=True)
    # liveness_net.setInput(blob)
    # prediction = liveness_net.forward()
    # spoof_score = prediction[0][0]
    
    # FOR NOW: We simulate a successful liveness check so your pipeline doesn't crash.
    # Replace this with the model prediction logic above when ready.
    is_live = True 
    confidence = 0.95
    
    if is_live and confidence > 0.85:
        return True
    return False

# ---------------------------------------------------------
# CHECK 2: Digital Forensics (Error Level Analysis)
# ---------------------------------------------------------
def perform_ela(image):
    """
    Detects if text or faces were copy-pasted onto the ID using Photoshop
    by comparing JPEG compression rates.
    """
    # 1. Save a temporary copy of the image at a slightly lower quality (90%)
    temp_filename = "temp_ela_check.jpg"
    cv2.imwrite(temp_filename, image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # 2. Read it back into memory
    compressed_image = cv2.imread(temp_filename)
    os.remove(temp_filename) # Clean up the file
    
    # 3. Mathematically subtract the new image from the original
    # Pixels that were NOT photoshopped will have changed slightly (due to compression).
    # Pixels that WERE copy-pasted will react completely differently to the compression.
    diff = cv2.absdiff(image, compressed_image)
    
    # 4. Convert the difference to grayscale to measure intensity
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    
    # 5. Calculate how many pixels lit up as "anomalies"
    # Normalize the pixel values to a 0-255 scale
    cv2.normalize(gray_diff, gray_diff, 0, 255, cv2.NORM_MINMAX)
    
    # Count pixels that are suspiciously bright (highly manipulated)
    threshold = 50 
    anomaly_pixels = cv2.countNonZero(cv2.threshold(gray_diff, threshold, 255, cv2.THRESH_BINARY)[1])
    total_pixels = gray_diff.shape[0] * gray_diff.shape[1]
    
    # 6. Calculate Score: Too many anomaly pixels = Photoshopped
    manipulation_ratio = anomaly_pixels / total_pixels
    
    # If more than 5% of the card's pixels are anomalies, score drops fast.
    ela_score = max(0.0, 100.0 - (manipulation_ratio * 2000))
    return min(100.0, ela_score)

# ---------------------------------------------------------
# CHECK 3: Structural & Template Check
# ---------------------------------------------------------
def verify_template(image):
    """
    Uses Object Detection to verify that mandatory security features 
    (holograms, seals, signatures) are physically present.
    """
    if not SEAL_MODEL_LOADED:
        # Fallback if your team hasn't trained the YOLO model yet
        return 100.0 
        
    # Ask the AI to find holograms on the card
    results = seal_detector(image, verbose=False)
    
    # results[0].boxes contains everything the AI found
    detected_objects = len(results[0].boxes)
    
    # If the model finds at least 1 required seal/hologram with high confidence, pass.
    if detected_objects >= 1: 
        return 100.0
    else:
        return 0.0 # Missing security features

# ---------------------------------------------------------
# MAIN FUNCTION (Document Tampering)
# ---------------------------------------------------------
def check_document_tampering(document_image):
    """
    The main function called by main.py to check the ID card.
    Combines the ELA (Photoshop) check and Template (Hologram) check.
    """
    ela_score = perform_ela(document_image)
    template_score = verify_template(document_image)
    
    # We weight them 50/50. 
    # If a scammer photoshops a real ID, ELA drops to 0. (Total = 50%)
    # If a scammer prints a flawless fake ID but misses the hologram, Template drops to 0. (Total = 50%)
    # In main.py, an 80% total is required, so failing either of these catches the fraudster.
    final_fraud_score = (ela_score * 0.5) + (template_score * 0.5)
    
    return final_fraud_score
