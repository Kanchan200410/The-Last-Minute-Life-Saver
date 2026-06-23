from flask import Flask, render_template, request, redirect
from database.supabase_client import supabase

app = Flask(__name__)


@app.route("/")
def dashboard():

    tasks = supabase.table("tasks").select("*").execute().data

    total_tasks = len(tasks)

    completed = len([
        task for task in tasks
        if task.get("status") == "Completed"
    ])

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

@app.route("/add-task")
def add_task_page():
    return render_template("add_task.html")


@app.route("/add-task", methods=["POST"])
def add_task():

    title = request.form["title"]
    description = request.form["description"]
    deadline = request.form["deadline"]

    supabase.table("tasks").insert({
        "title": title,
        "description": description,
        "deadline": deadline
    }).execute()

    return redirect("/")

@app.route("/tasks")
def tasks():

    tasks = (
        supabase
        .table("tasks")
        .select("*")
        .execute()
        .data
    )

    return render_template(
        "tasks.html",
        tasks=tasks
    )



if __name__ == "__main__":
    app.run(debug=True)