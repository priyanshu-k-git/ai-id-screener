from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# We will import our actual logic routes later when we build Phase 4
# from api.endpoints import router as kyc_router

# Initialize the FastAPI application
app = FastAPI(
    title="Enterprise KYC Verification Engine",
    description="Multi-modal document fraud detection and liveness pipeline.",
    version="1.0.0"
)

# ==========================================
# CORS Configuration (Critical for Frontend)
# ==========================================
# For a production app, you strictly limit these to your official website domains.
# For the hackathon, we whitelist the standard local development ports.
allowed_origins = [
    "http://localhost",
    "http://localhost:3000",   # Standard React port
    "http://localhost:5173",   # Standard Vite/React port
    "http://localhost:8501",   # Standard Streamlit port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],  # Allows all headers (including custom ones)
)


# ==========================================
# Server Health Check Route
# ==========================================
@app.get("/", tags=["System"])
async def root_health_check():
    """
    A simple heartbeat endpoint. When you start the server, ping this 
    in your browser to prove the API is alive and reachable.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "online",
            "service": "KYC Verification API",
            "message": "Core engine is running. Awaiting route registration from Phase 4."
        }
    )

# ==========================================
# Route Registration (Placeholder)
# ==========================================
# Once we build the api/endpoints.py file, we will connect it to the server here:
# app.include_router(kyc_router, prefix="/api/v1")
