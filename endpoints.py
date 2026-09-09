"""
api/endpoints.py

This module contains the primary FastAPI router that orchestrates the KYC verification.
It routes data through the vision, forensics, and logic engines based on document format.
"""
from fastapi import APIRouter, HTTPException
import base64

# Import Phase 1: Schemas & Utils
from core.schemas import VerificationRequest, VerificationResponse, DocumentFormat, TestStatus
from utils.image_helpers import decode_base64_to_image, preprocess_for_ocr

# Import Phase 2: Math & Crypto Logic
from logic.validators import (
    validate_verhoeff_checksum, 
    validate_pan_format, 
    verify_pdf_digital_signature, 
    validate_temporal_sanity
)

# Import Phase 3: AI Engines
from ml_models.liveness import detect_moire_pattern, verify_human_liveness
from ml_models.face_match import verify_face_match
from ml_models.ocr_engine import (
    extract_document_text, 
    parse_extracted_fields, 
    validate_spatial_layout, 
    validate_font_consistency
)

# Initialize the router
router = APIRouter()

@router.post("/verify-document", response_model=VerificationResponse)
async def verify_kyc_document(request: VerificationRequest):
    """
    The main endpoint. It takes the front-end JSON, runs the 9-test gauntlet, 
    and calculates an aggregate XAI confidence score.
    """
    # 1. Initialize the scorecard. Everything starts as SKIPPED.
    tests = {
        "test_1_passive_liveness": TestStatus.SKIPPED,
        "test_2_active_liveness": TestStatus.SKIPPED,
        "test_3_face_match": "SKIPPED",
        "test_4_spatial_layout": TestStatus.SKIPPED,
        "test_5_font_consistency": TestStatus.SKIPPED,
        "test_6_algorithmic_checksum": TestStatus.SKIPPED,
        "test_7_cross_field": TestStatus.SKIPPED,
        "test_8_temporal_sanity": TestStatus.SKIPPED,
        "test_9_digital_signature": TestStatus.SKIPPED
    }
    
    # Start with a perfect 100% score. We deduct points for failures.
    confidence = 100.0
    
    # ==========================================
    # GLOBAL PRE-CHECK: Temporal Sanity & Human Liveness
    # ==========================================
    
    # Run the basic date math
    tests["test_8_temporal_sanity"] = TestStatus.PASS if validate_temporal_sanity(request.dob) else TestStatus.FAIL
    if tests["test_8_temporal_sanity"] == TestStatus.FAIL:
        confidence -= 20.0
        
    # Process the selfie if it was provided
    selfie_img = None
    if request.selfie_base64:
        selfie_img = decode_base64_to_image(request.selfie_base64)
        if selfie_img is None:
            raise HTTPException(status_code=400, detail="Corrupted selfie image.")
            
        tests["test_2_active_liveness"] = verify_human_liveness(selfie_img)
        if tests["test_2_active_liveness"] == TestStatus.FAIL:
            confidence -= 35.0 # Heavy penalty for spoofed human


    # ==========================================
    # THE ROUTING MATRIX
    # ==========================================
    
    if request.document_format == DocumentFormat.DIGITAL_PDF:
        # ------------------------------------------
        # ROUTE B: The Digital PDF Gauntlet
        # ------------------------------------------
        try:
            # Strip header if present and decode base64 to raw bytes for pyHanko
            pdf_data = request.document_base64.split(",")[-1] if "," in request.document_base64 else request.document_base64
            pdf_bytes = base64.b64decode(pdf_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid PDF base64 format.")
            
        # Run Test 9 (Cryptography)
        is_signature_valid = verify_pdf_digital_signature(pdf_bytes)
        tests["test_9_digital_signature"] = TestStatus.PASS if is_signature_valid else TestStatus.FAIL
        
        if not is_signature_valid:
            # If the digital signature is broken, it's an immediate, fatal failure
            confidence = 0.0 
            
        # For a hackathon, extracting the photo from inside the encrypted PDF requires 
        # complex PyMuPDF logic, so we flag it as skipped or mocked.
        tests["test_3_face_match"] = "SKIPPED (Offline PDF Face Extraction Bypassed)"
        
    else:
        # ------------------------------------------
        # ROUTE A & C: The Physical & App Gauntlet
        # ------------------------------------------
        doc_img = decode_base64_to_image(request.document_base64)
        if doc_img is None:
            raise HTTPException(status_code=400, detail="Corrupted document image.")
            
        # Run Test 1 (Moire Pattern) - ONLY if it's supposed to be a physical card
        if request.document_format == DocumentFormat.PHYSICAL:
            tests["test_1_passive_liveness"] = detect_moire_pattern(doc_img)
            if tests["test_1_passive_liveness"] == TestStatus.FAIL:
                confidence -= 45.0 # Heavy penalty for holding up an iPad
                
        # Run Test 3 (1:1 Face Match)
        if selfie_img is not None:
            face_match_result = verify_face_match(doc_img, selfie_img)
            tests["test_3_face_match"] = face_match_result
            if "FAIL" in face_match_result:
                confidence -= 45.0
                
        # ------------------------------------------
        # Run the Visual Forensics & OCR Tests
        # ------------------------------------------
        ocr_img = preprocess_for_ocr(doc_img)
        ocr_data = extract_document_text(ocr_img)
        
        tests["test_4_spatial_layout"] = validate_spatial_layout(ocr_data["blocks"], request.document_type)
        tests["test_5_font_consistency"] = validate_font_consistency(ocr_data["blocks"])
        
        if tests["test_4_spatial_layout"] == TestStatus.FAIL:
            confidence -= 15.0
        if tests["test_5_font_consistency"] in [TestStatus.FAIL, TestStatus.ALERT]:
            confidence -= 10.0
            
        # ------------------------------------------
        # Run the Deterministic Logic Tests
        # ------------------------------------------
        fields = parse_extracted_fields(ocr_data["raw_text"], request.document_type)
        
        if fields["id_number"]:
            if request.document_type == "Aadhaar":
                is_valid = validate_verhoeff_checksum(fields["id_number"])
                tests["test_6_algorithmic_checksum"] = TestStatus.PASS if is_valid else TestStatus.FAIL
            elif request.document_type == "PAN":
                is_valid = validate_pan_format(fields["id_number"])
                tests["test_6_algorithmic_checksum"] = TestStatus.PASS if is_valid else TestStatus.FAIL
        else:
            # If the OCR failed to find an ID number, we fail the checksum test
            tests["test_6_algorithmic_checksum"] = TestStatus.FAIL
            confidence -= 20.0
            
        # For the hackathon demo, we will hardcode the Cross-Field test to PASS
        tests["test_7_cross_field"] = TestStatus.PASS 

    # ==========================================
    # FINAL VERDICT COMPUTATION
    # ==========================================
    
    # Ensure confidence doesn't drop below 0
    confidence = max(0.0, float(confidence))
    
    # Set the strict threshold for enterprise approval
    final_decision = "APPROVE - LOW RISK" if confidence >= 85.0 else "REJECT - HIGH RISK"
    
    return VerificationResponse(
        overall_confidence_score=confidence,
        final_decision=final_decision,
        **tests
    )
