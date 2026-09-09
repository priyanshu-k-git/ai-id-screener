import cv2
import numpy as np
import base64
import re
from typing import Optional

def decode_base64_to_image(base64_string: str) -> Optional[np.ndarray]:
    """
    Safely converts a base64 string from the frontend into an OpenCV Image (NumPy array).
    Strips out HTML data-URI headers if they exist.
    """
    try:
        # Check if the string contains the "data:image/jpeg;base64," header and strip it
        if "," in base64_string:
            base64_data = base64_string.split(",")[1]
        else:
            base64_data = base64_string
            
        # Decode the base64 string into raw bytes
        img_bytes = base64.b64decode(base64_data)
        
        # Convert bytes to a NumPy array
        np_arr = np.frombuffer(img_bytes, np.uint8)
        
        # Decode the NumPy array into an OpenCV image matrix (BGR format)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Decoded image is empty or corrupted.")
            
        return img
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return None


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Optimizes the document image for text extraction.
    OCR models struggle with shadows and color gradients. 
    This function converts the image to grayscale and applies adaptive thresholding.
    """
    # 1. Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 2. Apply a slight Gaussian blur to remove high-frequency camera noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 3. Apply Adaptive Thresholding to make text pop out against the background
    # This acts like a document scanner enhancement, forcing text to pure black and bg to pure white.
    processed = cv2.adaptiveThreshold(
        blurred, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    return processed


def preprocess_for_face_match(image: np.ndarray, target_size: tuple = (160, 160)) -> np.ndarray:
    """
    Optimizes the image for deep learning facial recognition models (like FaceNet).
    Biometric models usually require a specific input tensor size and RGB color space.
    """
    # OpenCV loads images in BGR format, but FaceNet expects RGB.
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Resize to the strict dimensions expected by the deep learning model
    resized = cv2.resize(rgb_image, target_size, interpolation=cv2.INTER_AREA)
    
    return resized


def encode_image_to_base64(image: np.ndarray, ext: str = ".jpg") -> str:
    """
    Converts an OpenCV image back to a base64 string.
    Useful if you want your API to return cropped bounding boxes to the frontend dashboard.
    """
    try:
        # Encode the OpenCV image matrix into a memory buffer
        _, buffer = cv2.imencode(ext, image)
        
        # Convert the buffer to a base64 string
        base64_str = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/{ext.strip('.')};base64,{base64_str}"
    except Exception as e:
        print(f"Error encoding image to base64: {e}")
        return ""
