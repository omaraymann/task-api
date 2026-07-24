from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Task API", version="1.0")

tasks = [
    {"id": 1, "title": "Learn FastAPI basics", "done": True},
    {"id": 2, "title": "Build the CRUD endpoints", "done": False},
    {"id": 3, "title": "Publish repo to GitHub", "done": False},
]

@app.get("/")
def read_root():
    """Describe the API: name, version, and available endpoints."""
    return {"name": "Task API", "version": "1.0", "endpoints":["/tasks"]}

@app.get("/health")
def health():
    """Check that the server is alive."""
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    """Return the full list of tasks."""
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Return one task by id. 404 if no task has that id."""
    task = next((task for task in tasks if task["id"] == task_id), None)
    if task is None:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    return task

@app.post("/tasks", status_code=201)
def create_task(task: dict):
    """Create a task from {"title": ...}. The server assigns the id and sets done to false. 400 if title is missing or empty."""
    title = task.get("title")
    if not isinstance(title, str) or not title.strip():
        return JSONResponse(status_code=400, content={"error": "title is required and must be a non-empty string"})

    new_task = {
        "id": max((t["id"] for t in tasks), default=0) + 1,
        "title": title.strip(),
        "done": False,
    }
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: dict):
    """Update a task's title and/or done. 404 if the id is unknown, 400 if the body is empty or invalid."""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    if "title" not in body and "done" not in body:
        return JSONResponse(status_code=400, content={"error": "body must contain title and/or done"})
    if "title" in body and (not isinstance(body["title"], str) or not body["title"].strip()):
        return JSONResponse(status_code=400, content={"error": "title must be a non-empty string"})
    if "done" in body and not isinstance(body["done"], bool):
        return JSONResponse(status_code=400, content={"error": "done must be true or false"})
    if "title" in body:
        task["title"] = body["title"].strip()
    if "done" in body:
        task["done"] = body["done"]
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by id. Returns 204 with no body, or 404 if the id is unknown."""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    tasks.remove(task)
