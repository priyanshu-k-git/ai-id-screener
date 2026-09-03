from deepface import DeepFace
import cv2
import numpy as np

# ---------------------------------------------------------
# GLOBAL AI MODEL INITIALIZATION
# ---------------------------------------------------------
print("Loading Facial Recognition Models...")
# We run a dummy verification on startup to force DeepFace to download 
# and load the ArcFace and RetinaFace weights into memory immediately.
# Otherwise, the first user who uploads an ID will have to wait 30 seconds.
try:
    dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
    DeepFace.verify(img1_path=dummy_img, img2_path=dummy_img, 
                    model_name="ArcFace", detector_backend="retinaface", 
                    enforce_detection=False)
except Exception:
    pass
print("Face Models loaded.")

# ---------------------------------------------------------
# MAIN FUNCTION (Biometric Match)
# ---------------------------------------------------------
def compare_faces(document_image, selfie_image):
    """
    Finds the faces in both images, extracts their vector embeddings, 
    and calculates the cosine similarity to verify identity.
    Called directly by main.py.
    """
    try:
        # DeepFace handles the detection, alignment, and math automatically.
        # - model_name="ArcFace": The industry standard for KYC/ID verification.
        # - detector_backend="retinaface": Highly accurate for finding faces on 
        #   complex ID card backgrounds.
        result = DeepFace.verify(
            img1_path=document_image, 
            img2_path=selfie_image, 
            model_name="ArcFace", 
            detector_backend="retinaface",
            enforce_detection=True # Triggers an error if a face is missing
        )
        
        # result is a dictionary. We care about the 'distance' metric.
        # Distance is how far apart the two faces are in the mathematical space.
        distance = result["distance"]
        threshold = result["threshold"]
        
        # Convert the raw distance into a 0-100 confidence score.
        # If the distance is exactly the threshold, confidence is 80%.
        # If the distance is 0 (identical twins/same photo), confidence is 100%.
        if distance >= threshold:
            # They don't match. Scale the score from 0 to 79.
            confidence = max(0.0, 80.0 * (1 - (distance - threshold)))
        else:
            # They match. Scale the score from 80 to 100.
            confidence = 80.0 + (20.0 * (1 - (distance / threshold)))
            
        return min(100.0, confidence)
        
    except ValueError as e:
        # This error triggers if RetinaFace scans the ID card or the selfie 
        # and absolutely cannot find a human face.
        print(f"Face Matching Error: {e}")
        return 0.0
    except Exception as e:
        # Catch-all for memory errors or corrupt image matrices
        print(f"System Error in Face Matcher: {e}")
        return 0.0
