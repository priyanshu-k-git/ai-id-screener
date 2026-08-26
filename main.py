from fastapi import FastAPI, UploadFile, File
import preprocessing
import fraud_detector
import ocr_engine
import face_matcher
import database_manager

app = FastAPI()

# Input: id_card (UploadFile), selfie (UploadFile) from the user
# Output: JSON Dictionary containing the final status, score, and breakdown
# Work: Orchestrates the entire pipeline. Cleans images -> Checks liveness -> 
# Runs parallel AI checks -> Calculates weighted score -> Saves to DB -> Returns response.
@app.post("/verify-identity")
async def verify_identity(id_card: UploadFile = File(...), selfie: UploadFile = File(...)):
    pass
