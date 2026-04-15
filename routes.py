
import uuid
from flask import Blueprint, request, jsonify
from models import create_task, get_task, list_tasks
from tasks import process_task

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

# Map priority names to Celery queue names
PRIORITY_TO_QUEUE = {
    "HIGH":   "high",
    "MEDIUM": "medium",
    "LOW":    "low",
}

# POST /tasks 
@tasks_bp.post("/")
def submit_task():
    """
    Submit a new task. Returns immediately.
    Processing happens asynchronously in the Celery worker.
    """
    data = request.get_json(force=True)
    priority = data.get("priority", "MEDIUM").upper()
    payload  = data.get("payload")

    if priority not in PRIORITY_TO_QUEUE:
        return jsonify({"error": "priority must be HIGH, MEDIUM, or LOW"}), 400

    if not payload or not isinstance(payload, dict):
        return jsonify({"error": "payload must be a JSON object"}), 400

    task = {
        "id":       str(uuid.uuid4()),
        "payload":  payload,
        "priority": priority,
        "status":   "PENDING",
    }

    
    create_task(task)

    # Send to the correct Celery queue based on priority
    # Celery uses this as a unique job ID.
    # If the same task_id is submitted twice, Celery won't create a duplicate job.
    # This is my idempotency key.
    queue = PRIORITY_TO_QUEUE[priority]
    process_task.apply_async(
        args=[task["id"]],
        queue=queue,
        task_id=task["id"],   # Makes the Celery job ID = our task ID
    )

    return jsonify({"id": task["id"], "status": "PENDING", "priority": priority}), 201


# GET /tasks/<id> 
@tasks_bp.get("/<task_id>")
def get_task_status(task_id):
    """Fetch a single task by ID. Poll this to track progress."""
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


# GET /tasks 
@tasks_bp.get("/")
def list_all_tasks():
    """
    List all tasks.
    Optional query params: ?status=PENDING&priority=HIGH
    """
    status   = request.args.get("status")
    priority = request.args.get("priority")
    tasks    = list_tasks(status=status, priority=priority)
    return jsonify(tasks)
