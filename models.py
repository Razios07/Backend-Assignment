
import sqlite3
import json

DB_PATH = "tasks.db"

def get_conn():
    # check_same_thread=False is needed because Flask may call this from different threads
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row   # Lets us access columns by name: row["status"]
    return conn

def init_db():
    """Create the tasks table if it doesn't exist yet."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          TEXT PRIMARY KEY,
                payload     TEXT NOT NULL,        -- stored as JSON string
                priority    TEXT NOT NULL,         -- HIGH / MEDIUM / LOW
                status      TEXT NOT NULL,         -- PENDING / PROCESSING / COMPLETED / FAILED
                retry_count INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    print("✅ Database ready.")

# CRUD helpers 

def create_task(task: dict):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tasks (id, payload, priority, status, retry_count) VALUES (?, ?, ?, ?, ?)",
            (task["id"], json.dumps(task["payload"]), task["priority"], task["status"], 0)
        )
        conn.commit()
    return task

def get_task(task_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        return None
    return _row_to_dict(row)

def update_task(task_id: str, fields: dict):
    """Dynamically update any fields. Only updates what's passed in."""
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [task_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        conn.commit()

def list_tasks(status: str = None, priority: str = None):
    conditions, values = [], []
    if status:
        conditions.append("status = ?")
        values.append(status)
    if priority:
        conditions.append("priority = ?")
        values.append(priority)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    with get_conn() as conn:
        rows = conn.execute(f"SELECT * FROM tasks {where} ORDER BY created_at DESC", values).fetchall()
    return [_row_to_dict(r) for r in rows]

def _row_to_dict(row) -> dict:
    d = dict(row)
    d["payload"] = json.loads(d["payload"])   # Parse JSON string back to dict
    return d
