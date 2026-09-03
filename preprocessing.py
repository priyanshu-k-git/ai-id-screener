import cv2
import numpy as np
from pdf2image import convert_from_bytes

# ---------------------------------------------------------
# HELPER 1: Handle Incoming Files (PDFs and Images)
# ---------------------------------------------------------
def load_file(file_bytes, content_type):
    """Converts FastAPI byte streams into an OpenCV image matrix."""
    if content_type == "application/pdf":
        # Convert first page of the PDF to an image
        pages = convert_from_bytes(file_bytes)
        # Convert PIL image to OpenCV format (RGB to BGR)
        img = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
        return img
    else:
        # It's a standard image (JPEG/PNG)
        np_arr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img

# ---------------------------------------------------------
# HELPER 2: Find the 4 Corners (Edge Detection)
# ---------------------------------------------------------
def order_points(pts):
    """Sorts corners into: Top-Left, Top-Right, Bottom-Right, Bottom-Left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)] # Top-Left has smallest x+y
    rect[2] = pts[np.argmax(s)] # Bottom-Right has largest x+y
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # Top-Right has smallest x-y
    rect[3] = pts[np.argmax(diff)] # Bottom-Left has largest x-y
    return rect

def get_document_corners(image):
    """Uses geometry to find the edges of the ID card."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 75, 200) # Draws sharp white lines on edges
    
    # Find contours (outlines)
    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # Sort them by area, keeping only the largest ones
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    for c in contours:
        # Approximate the contour shape
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
        # If the shape has exactly 4 corners, we found the ID card!
        if len(approx) == 4:
            return order_points(approx.reshape(4, 2))
            
    # Fallback: If it can't find 4 corners, just return the whole image boundaries
    h, w = image.shape[:2]
    return order_points(np.array([[0,0], [w,0], [w,h], [0,h]]))

# ---------------------------------------------------------
# HELPER 3: Flatten the Trapezium
# ---------------------------------------------------------
def warp_perspective(image, corners):
    """Stretches the skewed card into a flat 856x540 rectangle."""
    width, height = 856, 540 # Standard ID card ratio
    
    # Define the perfect flat rectangle
    destination_corners = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype="float32")
    
    # Calculate the stretch math and apply it
    matrix = cv2.getPerspectiveTransform(corners, destination_corners)
    flat_image = cv2.warpPerspective(image, matrix, (width, height))
    
    return flat_image

# ---------------------------------------------------------
# HELPER 4: Enhance for the AI Models
# ---------------------------------------------------------
def enhance_for_ai(image):
    """Fixes bad lighting to help the OCR engine read the text."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # This brightens shadows and darkens glare locally, rather than globally
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    return enhanced

# ---------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------
def process_document(file_bytes, content_type):
    """The only function main.py needs to call."""
    # 1. Load it
    raw_img = load_file(file_bytes, content_type)
    
    # 2. Find the ID card
    corners = get_document_corners(raw_img)
    
    # 3. Crop and flatten it
    flat_img = warp_perspective(raw_img, corners)
    
    # 4. Enhance the lighting
    final_clean_img = enhance_for_ai(flat_img)
    
    return final_clean_img
