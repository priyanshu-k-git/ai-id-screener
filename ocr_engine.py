import easyocr
import re
import cv2
from mrz.checker.td1 import TD1CodeChecker
from mrz.checker.td3 import TD3CodeChecker

# Initialize the AI model ONCE when the server starts.
# Loading this into memory takes a few seconds. If you put this inside 
# the function, the API will freeze for 5 seconds every time someone uploads an ID.
print("Loading OCR Model into memory...")
reader = easyocr.Reader(['en'], gpu=False) # Set gpu=True if running on a server with an NVIDIA GPU
print("OCR Model loaded successfully.")

# ---------------------------------------------------------
# HELPER 1: Extract Raw Text (The AI Reader)
# ---------------------------------------------------------
def get_raw_text(image):
    """Scans the image and extracts all visible text into a list of strings."""
    # detail=0 returns just the text, ignoring the bounding box coordinates
    text_results = reader.readtext(image, detail=0)
    
    # Combine the list into one giant block of text separated by newlines
    raw_text = "\n".join(text_results)
    return raw_text, text_results

# ---------------------------------------------------------
# HELPER 2: Parse the Data (The Regex Hunter)
# ---------------------------------------------------------
def parse_fields(raw_text, text_list):
    """Hunts for specific data patterns like Dates and the MRZ code."""
    extracted_data = {
        "dob": None,
        "mrz_lines": []
    }
    
    # 1. Find a Date of Birth (Looks for DD/MM/YYYY or DD-MM-YYYY)
    dob_match = re.search(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b', raw_text)
    if dob_match:
        extracted_data["dob"] = dob_match.group(0)

    # 2. Extract the Machine Readable Zone (MRZ)
    # The MRZ contains long strings of capital letters, numbers, and the "<" symbol.
    for line in text_list:
        # If a line has at least 15 characters and contains "<<", it's an MRZ line
        if len(line) >= 15 and "<" in line:
            # Strip out any random spaces EasyOCR might have accidentally added
            clean_line = line.replace(" ", "")
            extracted_data["mrz_lines"].append(clean_line)
            
    return extracted_data

# ---------------------------------------------------------
# HELPER 3: The Cryptographic Math (Anti-Fraud)
# ---------------------------------------------------------
def validate_mrz(mrz_lines):
    """Runs the checksum math on the MRZ to detect Photoshop tampering."""
    if not mrz_lines or len(mrz_lines) < 2:
        return False, 0.0 # No MRZ found, cannot verify integrity
    
    mrz_string = "\n".join(mrz_lines)
    
    try:
        # Try checking it as a standard 3-line ID Card (TD1 format)
        if len(mrz_lines) == 3:
            checker = TD1CodeChecker(mrz_string)
        # Try checking it as a standard 2-line Passport (TD3 format)
        elif len(mrz_lines) == 2:
            checker = TD3CodeChecker(mrz_string)
        else:
            return False, 0.0
            
        # bool(checker) runs the mathematical algorithm. 
        # Returns True if the math is perfect, False if it was forged.
        is_valid = bool(checker)
        return is_valid, 100.0 if is_valid else 0.0
        
    except Exception as e:
        # If the MRZ is corrupted or badly formatted, it fails the check
        return False, 0.0

# ---------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------
def extract_and_verify(preprocessed_image):
    """The only function main.py needs to call."""
    # 1. Read the text
    raw_text, text_list = get_raw_text(preprocessed_image)
    
    # 2. Extract the useful fields
    extracted_data = parse_fields(raw_text, text_list)
    
    # 3. Validate the mathematical integrity
    mrz_is_valid, integrity_score = validate_mrz(extracted_data["mrz_lines"])
    
    # Return the parsed data and the score back to the orchestrator
    return extracted_data, integrity_score
