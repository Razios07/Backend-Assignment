# Prioritized Async Task Processing System
### Built with Python · Flask · Celery · Redis · SQLite

# Install the required packages
pip install -r requirements.txt

## 🧠 Architecture (Simple Explanation)

```
User
 │
 ▼
Flask API  ──── writes ────▶  SQLite DB  (source of truth)
 │
 └── enqueues ──▶  Redis
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       [high]    [medium]     [low]
       queue      queue       queue
          │          │          │
          └──────────┴──────────┘
                     │
              Celery Worker(s)
              (always drain "high" first)
                     │
              updates status in SQLite
```

**In plain English:**
1. A user submits a task via POST /tasks
2. Flask saves it to SQLite with status = PENDING
3. Flask sends the task ID to the correct Redis queue (high/medium/low)
4. A Celery worker picks it up, processes it, and updates the status
5. The user can poll GET /tasks/{id} to check the status

The API returns instantly. All heavy lifting is done by the worker in the background.

