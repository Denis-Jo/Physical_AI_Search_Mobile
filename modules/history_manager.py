import json
import os
import threading
from datetime import datetime

HISTORY_FILE = "history.json"
_history_lock = threading.Lock()

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_to_history(item_type, title, link, source_or_author):
    with _history_lock:
        history = load_history()
        
        # Check if already exists to avoid duplicates
        for item in history:
            if item.get("link") == link:
                return False # Already saved
                
        new_item = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": item_type,
            "title": title,
            "link": link,
            "meta": source_or_author
        }
        history.insert(0, new_item) # Add to front
        
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
            
        return True

def get_history_by_date():
    history = load_history()
    grouped = {}
    for item in history:
        date_key = item['date'].split(" ")[0]
        if date_key not in grouped:
            grouped[date_key] = []
        grouped[date_key].append(item)
    return grouped
