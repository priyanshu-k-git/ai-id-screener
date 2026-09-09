"""
app.py

The main Streamlit dashboard. 
Run this via terminal: streamlit run app.py
"""
import streamlit as st
import requests
import json

# Import the camera components we built in File 9
from components.camera import render_live_capture_flow, render_pdf_upload_flow

# FastAPI Backend Endpoint URL
API_URL = "http://localhost:8000/api/v1/verify-document"

# Page Configuration
st.set_page_config(
    page_title="Enterprise KYC Verification Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Dark Mode Enterprise Aesthetic
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# Sidebar Navigation / Info
st.sidebar.title("🛡️ SecureKYC Engine")
st.sidebar.markdown("---")
st.sidebar.info(
    "This system uses a multi-modal pipeline combining computer vision "
    "for physical forgery detection, deep learning biometrics, and offline "
    "cryptographic Public Key Infrastructure (PKI) for digital documents."
)

st.title("Enterprise Identity Verification Dashboard")
st.markdown("Zero-trust automated document authentication and fraud screening system.")
st.markdown("---")

# ==========================================
# STAGE 1: THE INPUT FUNNEL
# ==========================================
st.subheader("Step 1: Identity Profile & Document Configuration")

col_a, col_b, col_c = st.columns(3)

with col_a:
    user_name = st.text_input("Full Legal Name", placeholder="e.g., Jane Doe")

with col_b:
    dob = st.text_input("Date of Birth (DD-MM-YYYY)", placeholder="DD-MM-YYYY")

with col_c:
    doc_type = st.selectbox(
        "Select ID Type",
        ["Aadhaar", "PAN", "Passport", "Driving License", "Voter ID"]
    )

# Dynamic Format Selection based on ID Type
format_mapping = {
    "Aadhaar": ["Physical/PVC", "Digital PDF", "Secure App/QR"],
    "PAN": ["Physical/PVC", "Digital PDF"],
    "Passport": ["Physical/PVC", "Digital PDF"],
    "Driving License": ["Physical/PVC", "Digital PDF"],
    "Voter ID": ["Physical/PVC", "Digital PDF"]
}

doc_format = st.selectbox(
    "Select Document Format", 
    format_mapping.get(doc_type, ["Physical/PVC", "Digital PDF"])
)

st.markdown("---")

# ==========================================
# STAGE 2: THE CAPTURE GATE
# ==========================================
document_b64 = None
selfie_b64 = None

if doc_format == "Digital PDF":
    # Route B: PDF Upload Flow
    document_b64, selfie_b64 = render_pdf_upload_flow()
else:
    # Route A & C: Live Camera Capture Flow
    document_b64, selfie_b64 = render_live_capture_flow()

st.markdown("---")

# ==========================================
# STAGE 3: API SUBMISSION & RESULTS
# ==========================================
if st.button("Execute Verification Pipeline", type="primary", use_container_width=True):
    if not user_name or not dob:
        st.error("Please enter the user's Full Name and Date of Birth.")
    elif not document_b64:
        st.error("Document data is missing. Please capture or upload your ID.")
    else:
        # Prepare the strict JSON payload matching core/schemas.py
        payload = {
            "user_name": user_name,
            "dob": dob,
            "document_type": doc_type,
            "document_format": doc_format,
            "document_base64": document_b64,
            "selfie_base64": selfie_b64
        }

        with st.spinner("Executing multi-modal AI and cryptographic gauntlet..."):
            try:
                response = requests.post(API_URL, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("Pipeline execution complete.")
                    st.markdown("---")
                    
                    # ==========================================
                    # STAGE 4: THE RESULTS DASHBOARD
                    # ==========================================
                    st.subheader("Explainable AI (XAI) Risk Matrix")
                    
                    # Top Section: Verdict & Overall Confidence
                    res_col1, res_col2 = st.columns([1, 2])
                    
                    with res_col1:
                        score = result["overall_confidence_score"]
                        decision = result["final_decision"]
                        
                        st.metric(label="Overall Confidence Score", value=f"{score:.1f}%")
                        
                        if "APPROVE" in decision:
                            st.success(f"**Verdict:** {decision}")
                        else:
                            st.error(f"**Verdict:** {decision}")

                    with res_col2:
                        st.markdown("**Executive Summary:**")
                        st.write(f"Document Type: `{doc_type} ({doc_format})`")
                        st.write(f"Identity Profile: `{user_name} (DOB: {dob})`")
                        st.write("All security layers have completed execution. Review individual test statuses below.")

                    st.markdown("### Detailed 9-Point Security Breakdown")
                    
                    # Bottom Section: The 9 Test Results Grid
                    tests_to_display = [
                        ("Test 1: Passive Liveness (Document Moire)", result["test_1_passive_liveness"]),
                        ("Test 2: Active Liveness (Human Depth)", result["test_2_active_liveness"]),
                        ("Test 3: 1:1 Biometric Face Match", result["test_3_face_match"]),
                        ("Test 4: Spatial Layout Template", result["test_4_spatial_layout"]),
                        ("Test 5: Font & Glyph Consistency", result["test_5_font_consistency"]),
                        ("Test 6: Algorithmic Checksum Validation", result["test_6_algorithmic_checksum"]),
                        ("Test 7: Cross-Field Data Consistency", result["test_7_cross_field"]),
                        ("Test 8: Temporal Sanity Check", result["test_8_temporal_sanity"]),
                        ("Test 9: Cryptographic PKI Signature", result["test_9_digital_signature"])
                    ]

                    # Render as clean rows
                    for test_name, status in tests_to_display:
                        col_t1, col_t2 = st.columns([3, 1])
                        with col_t1:
                            st.write(f"**{test_name}**")
                        with col_t2:
                            if status == "PASS":
                                st.success("PASS")
                            elif status == "FAIL":
                                st.error("FAIL")
                            elif status == "ALERT":
                                st.warning("ALERT")
                            else:
                                st.info(str(status))

                else:
                    st.error(f"Server Error ({response.status_code}): {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to the FastAPI backend. Ensure your Uvicorn server is running on port 8000.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
