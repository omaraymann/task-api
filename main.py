from fastapi import FastAPI
from fastapi.responses import JSONResponse

from db import SEED_TASKS, get_connection, init_db

app = FastAPI(title="Task API", version="1.0")

init_db()  # creates tasks.db and the tasks table on first run, seeds 3 tasks only when empty

def row_to_task(row):
    """Convert a sqlite3.Row into the task dict the API has always returned (done as a real bool, not 0/1)."""
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

@app.get("/")
def read_root():
    """Describe the API: name, version, and available endpoints."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks", "/stats", "/reset"]}

@app.get("/health")
def health():
    """Check that the server is alive."""
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks(done: bool | None = None, search: str | None = None):
    """Return the list of tasks. Optional filters: ?done=true|false and ?search=word (matches the title)."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    finally:
        conn.close()
    result = [row_to_task(r) for r in rows]
    if done is not None:
        result = [t for t in result if t["done"] == done]
    if search is not None and search.strip():
        result = [t for t in result if search.strip().lower() in t["title"].lower()]
    return result

@app.get("/stats")
def get_stats():
    """Compute task counts with SQL: total, done, and open."""
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        done_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
    finally:
        conn.close()
    return {"total": total, "done": done_count, "open": total - done_count}

@app.post("/reset")
def reset_tasks():
    """Restore the three seed tasks. Handy for demos."""
    conn = get_connection()
    try:
        with conn:  # transaction: wipe and re-seed all-or-nothing
            conn.execute("DELETE FROM tasks")
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'tasks'")  # ids start from 1 again
            conn.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS)
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    finally:
        conn.close()
    return [row_to_task(r) for r in rows]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Return one task by id. 404 if no task has that id."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    return row_to_task(row)

@app.post("/tasks", status_code=201)
def create_task(task: dict):
    """Create a task from {"title": ...}. The server assigns the id and sets done to false. 400 if title is missing or empty."""
    title = task.get("title")
    if not isinstance(title, str) or not title.strip():
        return JSONResponse(status_code=400, content={"error": "title is required and must be a non-empty string"})

    conn = get_connection()
    try:
        with conn:  # transaction: the insert is committed to disk before we respond
            cursor = conn.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?)", (title.strip(), 0)
            )
        new_id = cursor.lastrowid
    finally:
        conn.close()
    return {"id": new_id, "title": title.strip(), "done": False}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: dict):
    """Update a task's title and/or done. 404 if the id is unknown, 400 if the body is empty or invalid."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
        if "title" not in body and "done" not in body:
            return JSONResponse(status_code=400, content={"error": "body must contain title and/or done"})
        if "title" in body and (not isinstance(body["title"], str) or not body["title"].strip()):
            return JSONResponse(status_code=400, content={"error": "title must be a non-empty string"})
        if "done" in body and not isinstance(body["done"], bool):
            return JSONResponse(status_code=400, content={"error": "done must be true or false"})
        task = row_to_task(row)
        if "title" in body:
            task["title"] = body["title"].strip()
        if "done" in body:
            task["done"] = body["done"]
        with conn:  # transaction: write the merged task back to disk
            conn.execute(
                "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
                (task["title"], int(task["done"]), task_id),
            )
    finally:
        conn.close()
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by id. Returns 204 with no body, or 404 if the id is unknown."""
    conn = get_connection()
    try:
        with conn:  # transaction: commit the delete
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    finally:
        conn.close()
    if cursor.rowcount == 0:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
