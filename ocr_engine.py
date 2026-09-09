"""
ml_models/ocr_engine.py

This module handles Text Extraction (OCR), Spatial Layout Validation (Test 4),
and Font/Glyph Consistency (Test 5).
"""
import easyocr
import numpy as np
import re
from core.schemas import TestStatus

# Initialize the EasyOCR reader once in memory (Singleton pattern).
# Set gpu=True if your hackathon laptop has an Nvidia GPU, otherwise keep False.
try:
    reader = easyocr.Reader(['en'], gpu=False)
except Exception as e:
    print(f"Warning: OCR model failed to load. {e}")
    reader = None


def extract_document_text(image: np.ndarray) -> dict:
    """
    Runs the deep learning OCR engine on the preprocessed image.
    Returns a dictionary of raw OCR results including the bounding boxes.
    """
    if reader is None:
        return {"raw_text": "", "blocks": []}

    # readtext returns a list of tuples: (bounding_box, text, confidence)
    # bounding_box is a list of 4 points: [top-left, top-right, bottom-right, bottom-left]
    results = reader.readtext(image)
    
    extracted_data = {
        "raw_text": " ".join([res[1] for res in results]),
        "blocks": results
    }
    return extracted_data


def parse_extracted_fields(raw_text: str, doc_type: str) -> dict:
    """
    Uses Regex to hunt for the specific fields needed by validators.py.
    """
    fields = {
        "id_number": None,
        "dob": None
    }
    
    # 1. Find Date of Birth (DD/MM/YYYY or DD-MM-YYYY)
    dob_match = re.search(r'\b(\d{2}[-/]\d{2}[-/]\d{4})\b', raw_text)
    if dob_match:
        # Standardize the format for the temporal sanity check
        fields["dob"] = dob_match.group(1).replace('/', '-')
        
    # 2. Extract specific ID numbers
    if doc_type == "PAN":
        pan_match = re.search(r'\b([A-Z]{5}\d{4}[A-Z]{1})\b', raw_text.upper())
        if pan_match:
            fields["id_number"] = pan_match.group(1)
            
    elif doc_type == "Aadhaar":
        # Using a regex to find any 12-digit number (ignoring spaces)
        # Note: Do not hardcode actual numbers here, just the extraction logic.
        aadhaar_match = re.search(r'\b(\d{4}\s?\d{4}\s?\d{4})\b', raw_text)
        if aadhaar_match:
            fields["id_number"] = aadhaar_match.group(1).replace(' ', '')
            
    return fields


# ==========================================
# VISUAL FORENSICS (Tests 4 & 5)
# ==========================================

def validate_spatial_layout(ocr_blocks: list, doc_type: str) -> TestStatus:
    """
    Test 4: Spatial Layout Validation.
    Checks if the extracted bounding boxes align with the mathematical template.
    """
    if not ocr_blocks or len(ocr_blocks) < 3:
        return TestStatus.FAIL

    # For the hackathon, we simulate template validation by checking axial alignment.
    # If a fraudster pastes a new Date of Birth onto a card, human error usually 
    # places the bounding box a few pixels higher or lower than the original text line.
    
    # Extract the Y-coordinates of the top-left corner of every text block
    y_coordinates = [block[0][0][1] for block in ocr_blocks] 
    
    # If the variance of the text lines is completely chaotic, it suggests 
    # a poorly spliced composite image rather than a flat, printed card.
    variance = np.var(y_coordinates)
    
    if variance > 5000: # Threshold arbitrarily set for hackathon demo purposes
        return TestStatus.FAIL
        
    return TestStatus.PASS


def validate_font_consistency(ocr_blocks: list) -> TestStatus:
    """
    Test 5: Font & Glyph Consistency.
    Analyzes the confidence variance to catch mismatched anti-aliasing.
    """
    if not ocr_blocks:
        return TestStatus.FAIL
        
    # Hackathon Innovation: A pasted forgery often has a completely different resolution.
    # Deep learning OCRs return a confidence score based on character clarity. 
    # If the average confidence of the document is 95%, but the Date of Birth box 
    # has a confidence of 42% (because of digital edge-blurring from Photoshop),
    # we throw a visual anomaly ALERT.
    
    confidences = [block[2] for block in ocr_blocks]
    if not confidences:
        return TestStatus.FAIL
        
    avg_confidence = sum(confidences) / len(confidences)
    
    for conf in confidences:
        # If any single text block is drastically lower quality than the rest of the document:
        if conf < (avg_confidence - 0.35): 
            return TestStatus.ALERT # Needs human review by a compliance officer
            
    return TestStatus.PASS
