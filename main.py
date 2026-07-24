from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

tasks = [
    {"id": 1, "title": "Learn FastAPI basics", "done": True},
    {"id": 2, "title": "Build the CRUD endpoints", "done": False},
    {"id": 3, "title": "Publish repo to GitHub", "done": False},
]

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints":["/tasks"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = next((task for task in tasks if task["id"] == task_id), None)
    if task is None:
            return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    return task
