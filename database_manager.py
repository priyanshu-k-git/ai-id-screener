import sqlite3
import json

# Input: None
# Output: None
# Work: Connects to the SQLite database on server startup and creates the 'verifications' table if it doesn't already exist.
def setup_database():
    pass

# Input: final_report_dict (Dictionary containing scores, text, and final decision)
# Output: success (Boolean)
# Work: Called by main.py at the very end. Inserts the JSON report, decision, and timestamp into the database for auditing.
def save_record(final_report_dict):
    pass
