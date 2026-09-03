from fastapi import FastAPI, UploadFile, File, HTTPException
import preprocessing
import fraud_detector
import ocr_engine
import face_matcher
import database_manager

app = FastAPI(title="AI Document & Identity Verification API")

# Define allowed MIME types for validation
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}
ALLOWED_DOC_TYPES = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}

def validate_file(file: UploadFile, allowed_types: set):
    """Checks if the uploaded file matches the permitted formats."""
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415, 
            detail=f"Unsupported file type: {file.filename}. Allowed: {allowed_types}"
        )

@app.post("/verify-identity")
async def verify_identity(
    id_card: UploadFile = File(..., description="Upload ID document (JPG, PNG, PDF)"), 
    selfie: UploadFile = File(..., description="Upload live selfie (JPG, PNG)")
):
    # 1. Validate File Formats
    validate_file(id_card, ALLOWED_DOC_TYPES)
    validate_file(selfie, ALLOWED_IMAGE_TYPES)
    
    # 2. Extract Raw Bytes
    # Await the file read so FastAPI doesn't block the server while downloading
    id_bytes = await id_card.read()
    selfie_bytes = await selfie.read()
    
    # 3. Preprocessing (Cleans images and handles PDF-to-Image conversion)
    # We pass the content_type so preprocessing knows if it needs to convert a PDF
    clean_id = preprocessing.process_document(id_bytes, id_card.content_type)
    clean_selfie = preprocessing.process_document(selfie_bytes, selfie.content_type)
    
    # 4. Early Exit Liveness Check
    is_live = fraud_detector.check_liveness(clean_selfie)
    if not is_live:
        response = {"status": "Rejected", "reason": "Spoof detected in selfie."}
        database_manager.save_record(response)
        return response

    # 5. Parallel AI Checks
    fraud_score = fraud_detector.check_document_tampering(clean_id)
    ocr_data, ocr_confidence = ocr_engine.extract_and_verify(clean_id)
    face_score = face_matcher.compare_faces(clean_id, clean_selfie)

    # 6. Final Decision Logic (Weighted Score)
    final_score = (face_score * 0.40) + (fraud_score * 0.40) + (ocr_confidence * 0.20)
    
    status = "Approved" if final_score >= 80.0 else "Rejected"
    reason = "Identity verified successfully." if status == "Approved" else f"Confidence score too low: {final_score:.1f}%"

    # 7. Generate Final Report
    final_report = {
        "status": status,
        "score": round(final_score, 2),
        "reason": reason,
        "extracted_data": ocr_data,
        "breakdown": {
            "face_match": round(face_score, 2),
            "document_integrity": round(fraud_score, 2),
            "ocr_readability": round(ocr_confidence, 2)
        }
    }

    # 8. Log and Return
    database_manager.save_record(final_report)
    return final_report
