from flask import Blueprint, render_template
from database.supabase_client import supabase

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)

@dashboard_bp.route("/dashboard")
def dashboard():

    tasks = supabase.table("tasks").select("*").execute().data

    total_tasks = len(tasks)

    completed = len(
        [t for t in tasks if t["status"] == "Completed"]
    )

    pending = total_tasks - completed

    productivity_score = (
        int((completed / total_tasks) * 100)
        if total_tasks > 0 else 0
    )

    return render_template(
        "dashboard.html",
        tasks=tasks,
        total_tasks=total_tasks,
        completed=completed,
        pending=pending,
        productivity_score=productivity_score
    )