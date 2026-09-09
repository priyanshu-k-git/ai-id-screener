"""
logic/validators.py

This module contains the deterministic mathematical checks for government IDs.
It executes offline validations without pinging any external databases.
"""
import re
import io
from datetime import datetime

# Required for offline PKI signature verification
# Install via: pip install pyHanko pyhanko-certvalidator
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature

# ==========================================
# VERHOEFF ALGORITHM (Checksum Logic)
# ==========================================
# The Verhoeff algorithm is a robust checksum formula used for 12-digit Indian IDs 
# (like [Aadhaar Redacted]) to catch accidental typos and fabricated numbers.

# The multiplication table (d)
VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]

# The permutation table (p)
VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]

def validate_verhoeff_checksum(id_number: str) -> bool:
    """
    Runs the deterministic Verhoeff checksum.
    Returns True if mathematically valid, False otherwise.
    """
    if not id_number.isdigit():
        return False
        
    c = 0
    # Reverse the string and iterate
    reversed_num = list(map(int, reversed(id_number)))
    for i, n in enumerate(reversed_num):
        c = VERHOEFF_D[c][VERHOEFF_P[i % 8][n]]
        
    # The checksum evaluates to 0 if the number is mathematically valid
    return c == 0


# ==========================================
# PAN CARD REGEX (Format Logic)
# ==========================================

def validate_pan_format(pan_number: str) -> bool:
    """
    Verifies that a PAN card follows the strict government template:
    5 Letters, 4 Numbers, 1 Letter (e.g., ABCDE1234F).
    """
    # Regex pattern mapping the precise format
    pattern = r"^[A-Z]{5}\d{4}[A-Z]{1}$"
    return bool(re.match(pattern, pan_number.upper().strip()))


# ==========================================
# PKI DIGITAL SIGNATURE (Crypto Logic)
# ==========================================

def verify_pdf_digital_signature(pdf_bytes: bytes) -> bool:
    """
    Offline PKI Validation for digital PDFs (like e-PAN or e-EPIC).
    Uses pyHanko to verify the embedded cryptographic signature.
    """
    try:
        # Load the PDF file from the byte stream
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfFileReader(pdf_stream)
        
        # Extract all embedded digital signatures from the PDF
        signatures = reader.embedded_signatures
        
        if not signatures:
            # If there is no signature, it is not a verified digital document
            return False
            
        for sig in signatures:
            # Run the cryptographic integrity check.
            # (Note: In a production environment, you would supply a ValidationContext 
            # containing the government's official root certificates here).
            status = validate_pdf_signature(sig)
            
            # The bottom_line attribute verifies that the hash is unbroken.
            if status.bottom_line:
                return True
                
        return False
        
    except Exception as e:
        print(f"Cryptographic verification failed: {e}")
        return False


# ==========================================
# TEMPORAL SANITY (Date Logic)
# ==========================================

def validate_temporal_sanity(dob_string: str) -> bool:
    """
    Ensures the extracted Date of Birth is logically possible.
    Expects a DD-MM-YYYY string.
    """
    try:
        dob = datetime.strptime(dob_string, "%d-%m-%Y")
        today = datetime.today()
        
        # A user cannot be born in the future
        if dob > today:
            return False
            
        # Hard check rejecting biologically impossible ages
        age = today.year - dob.year
        if age > 130:
            return False
            
        return True
    except ValueError:
        # Fails instantly if the date format is completely invalid (e.g., 35-13-2024)
        return False
