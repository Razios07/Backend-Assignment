# app.py — Entry point. Starts Flask, sets up DB, registers routes.

from flask import Flask
from models import init_db
from routes import tasks_bp

app = Flask(__name__)

# Register all /tasks routes from routes.py
app.register_blueprint(tasks_bp)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    init_db()          # Create SQLite table if it doesn't exist
    app.run(port=3000, debug=True)
