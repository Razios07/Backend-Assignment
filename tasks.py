
import random
import time
from celery_app import celery
from models import init_db, get_task, update_task

# Ensure DB is available in the worker process too
init_db()

@celery.task(
    bind=True,           
    max_retries=3,       
    name="process_task", 

def process_task(self, task_id: str):
    """
    The core worker function.
    1. Marks task as PROCESSING
    2. Simulates work (may fail ~30% of the time)
    3. Marks COMPLETED or retries on failure
    """
    print(f"⚙️  Processing task {task_id} (attempt {self.request.retries + 1})")

    # ── Idempotency check ────────────────────────────────────────────────────

    task = get_task(task_id)
    if not task:
        print(f"⚠️  Task {task_id} not found in DB — skipping.")
        return

    if task["status"] == "COMPLETED":
        print(f"⏭️  Task {task_id} already completed — skipping (idempotency guard).")
        return

    # Mark as PROCESSING so the API shows real-time status
    update_task(task_id, {"status": "PROCESSING", "retry_count": self.request.retries})

   
    # WHY simulate? In real systems, 3rd party APIs, DB writes, network calls can fail.
    # We need to test that our retry system works.
    if random.random() < 0.3:
        print(f"❌ Task {task_id} failed (simulated). Retrying if attempts remain...")

        try:
            # self.retry() re-queues this exact task with exponential backoff
            # countdown=2**retries gives: 1s → 2s → 4s between retries
            raise self.retry(countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            # All 3 retries used up — mark permanently FAILED
            update_task(task_id, {
                "status": "FAILED",
                "retry_count": self.request.retries
            })
            print(f"💀 Task {task_id} permanently FAILED after {self.request.retries} retries.")
            return

    
    time.sleep(0.5)  # Replace with real business logic (DB write, API call, etc.)

    # Mark COMPLETED only after successful processing — never before
    update_task(task_id, {"status": "COMPLETED", "retry_count": self.request.retries})
    print(f"✅ Task {task_id} COMPLETED.")
