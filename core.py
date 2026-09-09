from pydantic import BaseModel, Field, model_validator
from enum import Enum
from typing import Optional

# ==========================================
# INPUT ENUMS (The Routing Funnel)
# ==========================================

class DocumentType(str, Enum):
    AADHAAR = "Aadhaar"
    PAN = "PAN"
    PASSPORT = "Passport"
    DRIVING_LICENSE = "Driving License"
    VOTER_ID = "Voter ID"

class DocumentFormat(str, Enum):
    PHYSICAL = "Physical/PVC"
    DIGITAL_PDF = "Digital PDF"
    SECURE_APP = "Secure App/QR"


# ==========================================
# INPUT SCHEMA (What the Frontend Sends)
# ==========================================

class VerificationRequest(BaseModel):
    """
    The strict JSON payload expected from the frontend capture wizard.
    """
    user_name: str = Field(..., description="Full legal name (used for silent PDF decryption)")
    dob: str = Field(..., description="Date of birth in DD-MM-YYYY (used for silent PDF decryption)")
    
    document_type: DocumentType = Field(..., description="The type of ID being verified")
    document_format: DocumentFormat = Field(..., description="Determines which security gauntlet runs")
    
    # Base64 encoded strings
    document_base64: str = Field(..., description="Base64 encoded string of the document image or PDF file")
    selfie_base64: Optional[str] = Field(None, description="Base64 encoded live selfie (Required for vision checking)")

    @model_validator(mode='after')
    def validate_selfie_requirement(self):
        """
        Hard Logic Check: If the user selected a physical format or secure app, 
        they MUST provide a live selfie for liveness and biometric matching.
        """
        if self.document_format in [DocumentFormat.PHYSICAL, DocumentFormat.SECURE_APP]:
            if not self.selfie_base64:
                raise ValueError("A live selfie (selfie_base64) is strictly required for physical or app-based formats.")
        return self


# ==========================================
# OUTPUT ENUMS (The Explainable AI Matrix)
# ==========================================

class TestStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ALERT = "ALERT"      # Used for anomalies that need human review
    SKIPPED = "SKIPPED"  # Used when a test is bypassed (e.g., vision tests on a digital PDF)


# ==========================================
# OUTPUT SCHEMA (What the Dashboard Reads)
# ==========================================

class VerificationResponse(BaseModel):
    """
    The comprehensive 10-point Risk Matrix returned to the frontend dashboard.
    """
    # 1. Aggregate Score
    overall_confidence_score: float = Field(..., ge=0, le=100, description="Final aggregate percentage (0-100)")
    final_decision: str = Field(..., description="'APPROVE - LOW RISK' or 'REJECT - HIGH RISK'")
    
    # 2. The 9 Security Tests
    test_1_passive_liveness: TestStatus = Field(..., description="Moire/Screen replay detection")
    test_2_active_liveness: TestStatus = Field(..., description="Human depth/texture verification")
    test_3_face_match: str = Field(..., description="String containing percentage match or failure reason")
    test_4_spatial_layout: TestStatus = Field(..., description="Bounding box template alignment")
    test_5_font_consistency: TestStatus = Field(..., description="Kerning and glyph anomaly detection")
    test_6_algorithmic_checksum: TestStatus = Field(..., description="Cryptographic math validation of ID number")
    test_7_cross_field: TestStatus = Field(..., description="Visible text vs MRZ/QR consistency")
    test_8_temporal_sanity: TestStatus = Field(..., description="Issue dates vs visual age / DOB math")
    test_9_digital_signature: TestStatus = Field(..., description="PKI Certificate validation for PDFs/QRs")
