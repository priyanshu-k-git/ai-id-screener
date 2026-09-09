"""
ml_models/face_match.py

This module handles Test 3: 1:1 Biometric Face Matching.
It extracts the face from the ID document and compares it to the live selfie.
"""
import numpy as np
from deepface import DeepFace

def verify_face_match(document_img: np.ndarray, selfie_img: np.ndarray) -> str:
    """
    Compares the face printed on the ID card with the live webcam selfie.
    Returns a formatted string for the XAI Dashboard (e.g., "94% Match (PASS)").
    """
    try:
        # DeepFace.verify automatically detects the face, crops it, aligns it, 
        # and generates high-dimensional embeddings (using ArcFace by default here).
        # We set enforce_detection=True so it strictly fails if no face is found.
        
        result = DeepFace.verify(
            img1_path=document_img, 
            img2_path=selfie_img, 
            model_name="ArcFace",          # ArcFace is highly accurate for ID cards
            detector_backend="retinaface", # RetinaFace is excellent at finding tiny ID photos
            enforce_detection=True,
            distance_metric="cosine"
        )
        
        # 'verified' is a boolean based on a strict mathematical threshold
        is_match = result.get("verified", False)
        
        # Convert the mathematical distance into a human-readable confidence percentage.
        # DeepFace returns distance (lower is better). We invert it for a % score.
        distance = result.get("distance", 1.0)
        confidence_score = max(0.0, (1.0 - distance)) * 100
        
        if is_match:
            return f"{confidence_score:.1f}% Match (PASS)"
        else:
            return f"{confidence_score:.1f}% Match (FAIL - Faces do not match)"
            
    except ValueError as e:
        # This triggers if 'retinaface' cannot find a face in either the ID or the selfie.
        # This is a critical security tripwire. If a fraudster uploads a picture of a 
        # credit card instead of an ID, this catches it.
        print(f"Face extraction failed: {e}")
        return "FAIL (No human face detected in one or both images)"
    except Exception as e:
        print(f"Biometric engine error: {e}")
        return "FAIL (Biometric processing error)"
