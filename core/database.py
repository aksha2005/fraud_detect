import sqlite3
import re
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "campus_shield.db"

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, 
                  amount_protected REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS vouches
                 (hash TEXT PRIMARY KEY, 
                  vouched_at TEXT)''')
    conn.commit()
    conn.close()

def extract_amount(text: str) -> float:
    text_lower = text.lower()
    matches = re.findall(r"(?:₹|rs\.?|rupees)\s*([\d,]+(?:\.\d+)?)", text_lower)
    total = 0.0
    for m in matches:
        val = m.replace(',', '')
        try: total += float(val)
        except ValueError: pass
    
    lakh_matches = re.findall(r"([\d,]+(?:\.\d+)?)\s*(?:lakh|lakhs)", text_lower)
    for m in lakh_matches:
        val = m.replace(',', '')
        try: total += float(val) * 100000
        except ValueError: pass

    crore_matches = re.findall(r"([\d,]+(?:\.\d+)?)\s*(?:crore|crores)", text_lower)
    for m in crore_matches:
        val = m.replace(',', '')
        try: total += float(val) * 10000000
        except ValueError: pass

    return total

def log_scan_amount(amount: float):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO scans (timestamp, amount_protected) VALUES (?, ?)", 
              (datetime.now().isoformat(), amount))
    conn.commit()
    conn.close()

def get_total_wealth() -> float:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(amount_protected) FROM scans")
    res = c.fetchone()[0]
    conn.close()
    return res if res else 0.0

def add_vouch(text_hash: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO vouches (hash, vouched_at) VALUES (?, ?)", 
              (text_hash, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_vouch_age_days(text_hash: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT vouched_at FROM vouches WHERE hash = ?", (text_hash,))
    res = c.fetchone()
    conn.close()
    if res:
        vouched_at = datetime.fromisoformat(res[0])
        return (datetime.now() - vouched_at).days
    return None
