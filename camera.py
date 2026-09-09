"""
components/camera.py

This module handles the frontend live-capture workflow.
It uses Streamlit's native camera input to force real-time image capture
and prevents file uploads for physical documents.
"""
import streamlit as st
import base64

def get_base64_from_image(image_file):
    """
    Helper function to convert Streamlit's image object into a base64 string
    that our FastAPI backend expects.
    """
    if image_file is not None:
        bytes_data = image_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_str}"
    return None

def render_live_capture_flow():
    """
    Renders the step-by-step camera capture process in the Streamlit UI.
    Requires the user to take a photo of the ID first, then a selfie.
    """
    st.markdown("### 📷 Live Verification Workflow")
    st.info("To prevent fraud, file uploads are disabled for physical cards. Please use your webcam.")
    
    # Initialize session states to hold the images while the user navigates steps
    if 'doc_b64' not in st.session_state:
        st.session_state.doc_b64 = None
    if 'selfie_b64' not in st.session_state:
        st.session_state.selfie_b64 = None

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Step 1: Capture ID Document**")
        st.write("Hold your physical ID card clearly in front of the camera.")
        
        # This opens the browser's webcam. It cannot be spoofed by a file upload.
        doc_image = st.camera_input("Take ID Photo", key="cam_doc")
        
        if doc_image:
            st.session_state.doc_b64 = get_base64_from_image(doc_image)
            st.success("Document captured successfully!")

    with col2:
        st.markdown("**Step 2: Live Selfie**")
        st.write("Look directly into the camera for the liveness check.")
        
        # We only let them take a selfie AFTER they capture the document
        if st.session_state.doc_b64:
            selfie_image = st.camera_input("Take Live Selfie", key="cam_selfie")
            
            if selfie_image:
                st.session_state.selfie_b64 = get_base64_from_image(selfie_image)
                st.success("Selfie captured successfully!")
        else:
            st.warning("Please capture your ID document first.")

    # Return the encoded strings so app.py can send them to FastAPI
    return st.session_state.doc_b64, st.session_state.selfie_b64


def render_pdf_upload_flow():
    """
    Alternative workflow strictly for Digital PDFs (e-PAN, e-Aadhaar).
    This bypasses the camera for the document, but still requires a live selfie.
    """
    st.markdown("### 📄 Digital PDF Workflow")
    st.info("Upload your official government PDF. It will be verified via offline cryptography.")
    
    if 'pdf_b64' not in st.session_state:
        st.session_state.pdf_b64 = None
    if 'selfie_b64' not in st.session_state:
        st.session_state.selfie_b64 = None

    # Restrict uploads STRICTLY to PDFs. No JPGs allowed.
    uploaded_pdf = st.file_uploader("Upload Digital ID (PDF only)", type=["pdf"])
    
    if uploaded_pdf:
        # Convert PDF bytes to base64
        bytes_data = uploaded_pdf.getvalue()
        base64_str = base64.b64encode(bytes_data).decode('utf-8')
        st.session_state.pdf_b64 = f"data:application/pdf;base64,{base64_str}"
        st.success("PDF loaded securely.")
        
        st.markdown("---")
        st.markdown("**Step 2: Live Selfie**")
        st.write("Even with a digital PDF, we must verify you are the owner.")
        selfie_image = st.camera_input("Take Live Selfie for Biometric Match", key="cam_pdf_selfie")
        
        if selfie_image:
            st.session_state.selfie_b64 = get_base64_from_image(selfie_image)
            st.success("Selfie captured successfully!")

    return st.session_state.pdf_b64, st.session_state.selfie_b64
