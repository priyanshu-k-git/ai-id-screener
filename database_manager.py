import sqlite3
import json
from datetime import datetime

# ---------------------------------------------------------
# HELPER 1: Setup the Database and Table
# ---------------------------------------------------------
def setup_database():
    """
    Creates the SQLite database and the audit log table if they don't exist.
    This should be called once when the FastAPI server starts.
    """
    # Connects to the file (or creates it if it doesn't exist)
    conn = sqlite3.connect("kyc_audit_logs.db")
    
    # Best Practice: Enable WAL mode for better read/write concurrency
    conn.execute("PRAGMA journal_mode=WAL;") 
    
    cursor = conn.cursor()
    
    # Create the verifications table
    # We store the most important metrics as separate columns so they can be 
    # easily searched, and we store the rest of the data as a JSON string.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            final_score REAL NOT NULL,
            detailed_report TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# MAIN FUNCTION (Save the Verification Record)
# ---------------------------------------------------------
def save_record(final_report_dict):
    """
    Called by main.py at the very end of the pipeline.
    Safely inserts the AI's final decision into the database.
    """
    conn = None
    try:
        conn = sqlite3.connect("kyc_audit_logs.db")
        cursor = conn.cursor()
        
        # 1. Extract the key data points to make the database easily searchable
        # We use ISO-8601 format for timestamps so they sort perfectly
        current_time = datetime.now().isoformat() 
        status = final_report_dict.get("status", "Unknown")
        score = final_report_dict.get("score", 0.0)
        
        # 2. Convert the entire Python dictionary into a JSON string
        # This allows us to save the OCR text and the individual AI scores in one column
        details_json = json.dumps(final_report_dict)
        
        # 3. Insert the data securely
        # Using the (?) syntax is critical—it prevents SQL Injection attacks
        cursor.execute('''
            INSERT INTO verifications (timestamp, status, final_score, detailed_report)
            VALUES (?, ?, ?, ?)
        ''', (current_time, status, score, details_json))
        
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"Database insertion failed: {e}")
        
    finally:
        # Always close the connection even if the code crashes
        if conn:
            conn.close()

# ---------------------------------------------------------
# HELPER 2: Retrieve Records (For the Audit Trail)
# ---------------------------------------------------------
def get_recent_records(limit=10):
    """
    Allows an admin or dashboard to pull the most recent verification attempts.
    """
    try:
        conn = sqlite3.connect("kyc_audit_logs.db")
        cursor = conn.cursor()
        
        # Fetch the records, sorted by newest first
        cursor.execute('''
            SELECT id, timestamp, status, final_score, detailed_report 
            FROM verifications 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        return rows
        
    except sqlite3.Error as e:
        print(f"Failed to retrieve records: {e}")
        return []
        
    finally:
        if conn:
            conn.close()
