import cv2
import numpy as np

# Input: upload_file (FastAPI UploadFile byte stream)
# Output: cv2 image matrix (NumPy array)
# Work: Converts the raw web file bytes into an OpenCV image format.
def read_image_file(upload_file):
    pass

# Input: image (cv2 image matrix)
# Output: List of 4 coordinates [top-left, top-right, bottom-right, bottom-left]
# Work: Uses Edge Detection or a YOLO model to find the four corners of the ID card, ignoring the background.
def get_document_corners(image):
    pass

# Input: image (cv2 image matrix), corners (List of 4 coordinates)
# Output: cropped_image (cv2 image matrix)
# Work: Applies Perspective Transform to stretch a skewed/angled ID card into a perfectly flat rectangle.
def warp_perspective(image, corners):
    pass

# Input: cropped_image (cv2 image matrix)
# Output: enhanced_image (cv2 image matrix)
# Work: Adjusts brightness, increases contrast, and sharpens text to prepare the image for the OCR AI.
def enhance_for_ai(cropped_image):
    pass

# Input: upload_file (FastAPI UploadFile byte stream)
# Output: final_image (cv2 image matrix)
# Work: The master function called by main.py. Chains the read, crop, warp, and enhance functions together.
def process_document(upload_file):
    pass
