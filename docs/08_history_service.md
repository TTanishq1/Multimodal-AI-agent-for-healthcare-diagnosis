# History Service Documentation (app/services/history_service.py)
## Hinglish में Complete Explanation

### Overview (समझाइश)
`history_service.py` yeh file patient visits ko SQLite database mein store karti hai aur previous history fetch karti hai.

### Main Functions

**save_visit()** - Current visit ko database mein save karta hai
**get_history_summary()** - Previous visits ka summary return karta hai

**Lines 18-36: Database Setup**
```python
DB_PATH = Path(os.getenv("PATIENT_HISTORY_DB", "patient_history.db"))

def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            timestamp TEXT,
            transcript TEXT,
            image_summary TEXT,
            fusion_result_json TEXT
        )
    """)
    return conn
```
- SQLite database setup
- Table create karta hai (agar na ho)

**Lines 39-62: Save Visit**
```python
def save_visit(
    patient_id: Optional[str],
    transcript: str,
    image_summary: str,
    fusion_result: Dict[str, Any],
    timestamp: str,
) -> None:
```
- Visit data ko database mein insert karta hai
- JSON format mein fusion result store karta hai

**Lines 65-102: Get History Summary**
```python
def get_history_summary(patient_id: Optional[str]) -> str:
```
- Last 3 visits fetch karta hai
- Diagnoses ko summary format mein return karta hai
- Format: "Previous visits suggest: diagnosis1 (timestamp1); diagnosis2 (timestamp2); ..."

---

## Database Schema
- `id` - Auto-increment primary key
- `patient_id` - Patient identifier
- `timestamp` - Visit timestamp
- `transcript` - Patient's audio transcript
- `image_summary` - Image analysis summary
- `fusion_result_json` - Complete diagnosis (JSON)

---

## Usage
```python
from app.services.history_service import save_visit, get_history_summary

# Save visit
save_visit(
    patient_id="patient123",
    transcript="I have a wart",
    image_summary="Wart on foot",
    fusion_result={"preliminary_diagnosis": "Plantar wart"},
    timestamp="2025-12-04T22:00:00"
)

# Get history
history = get_history_summary("patient123")
```

