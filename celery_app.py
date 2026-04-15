
# Celery workers can be told to prefer "high" over "medium" over "low".
# This is better than sorting — items in "high" queue are always picked first.

from celery import Celery
from kombu import Queue

# Redis is both the broker (sends jobs) and backend (stores results)
REDIS_URL = "redis://localhost:6379/0"

celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

celery.conf.update(
    # Define 3 named queues — one per priority level
    task_queues=(
        Queue("high"),
        Queue("medium"),
        Queue("low"),
    ),

    
    task_default_queue="medium",

    
    # This is Celery's built-in way to enforce priority — no code sorting needed.
    task_queue_order_for_processing=["high", "medium", "low"],

    # Serialization format — JSON is readable and safe
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # The job is only "acknowledged" (removed from queue)
    # AFTER the worker finishes processing it — not before.
    # This means if a worker crashes mid-job, Redis still has the job and re-delivers it.
    # This is what gives us "at-least-once" processing.
    task_acks_late=True,

    # Each worker takes only ONE job at a time.
    # Without this, a worker might grab 4 jobs at once and hold them even if idle.
    worker_prefetch_multiplier=1,
)
