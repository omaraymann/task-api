import sqlite3
from pathlib import Path

# The whole database is this one file, created automatically on first run.
DB_PATH = Path(__file__).parent / "tasks.db"

SEED_TASKS = [
    ("Learn FastAPI basics", 1),
    ("Build the CRUD endpoints", 0),
    ("Publish repo to GitHub", 0),
]


def get_connection():
    """Open a connection to tasks.db. Rows come back as dict-like sqlite3.Row objects."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the tasks table if it's missing, and seed three example tasks only when the table is empty."""
    conn = get_connection()
    try:
        with conn:  # transaction: table + seed happen all-or-nothing
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            if count == 0:
                conn.executemany(
                    "INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS
                )
    finally:
        conn.close()
