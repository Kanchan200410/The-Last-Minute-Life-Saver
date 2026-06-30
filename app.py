import os

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for
)

from database.supabase_client import supabase
from services.gemini_service import generate_schedule
from services.time_estimator import estimate_task

from services.calendar_service import (
    get_calendar_service,
    get_upcoming_events,
    create_calendar_event
)
import datetime
from flask import jsonify
from services.priority_engine import generate_priority
from authlib.integrations.flask_client import OAuth
from config import Config
from database.user_db import get_user, update_profile
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)
app.secret_key = "last_minute_life_saver_secret"

app.config["GOOGLE_CLIENT_ID"] = Config.GOOGLE_CLIENT_ID
app.config["GOOGLE_CLIENT_SECRET"] = Config.GOOGLE_CLIENT_SECRET

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile https://www.googleapis.com/auth/calendar"
    }
)


# ==========================
# AUTHENTICATION ROUTES
# ==========================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():

    redirect_uri = url_for("callback", _external=True)

    return google.authorize_redirect(redirect_uri)

@app.route("/callback")
def callback():
    token = google.authorize_access_token()

    user = token["userinfo"]

    # Save user
    session["user"] = user

    # Save Google OAuth token
    session["google_token"] = token

    # TEMPORARY - check the token in terminal
    print(session["google_token"])

    # Check if user already exists
    existing_user = (
        supabase
        .table("users")
        .select("*")
        .eq("email", user["email"])
        .execute()
    )

    if len(existing_user.data) == 0:
        supabase.table("users").insert({

            "google_id": user["sub"],
            "name": user["name"],
            "email": user["email"],
            "picture": user["picture"]

        }).execute()

    # Get the user's database record
    db_user = (
        supabase
        .table("users")
        .select("*")
        .eq("email", user["email"])
        .single()
        .execute()
    )

    # Save database user in session
    session["db_user"] = db_user.data

    return redirect("/dashboard")



# ==========================================
# DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():
    user_id = session["db_user"]["id"]

    tasks = (
        supabase
        .table("tasks")
        .select("*")
        .eq("user_id", user_id)
        .execute()
        .data
    )

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

    try:

        calendar_events = get_upcoming_events(100)

        print("\n========================")
        print("DASHBOARD CALENDAR DATA")
        print("========================")
        print("TOTAL EVENTS:", len(calendar_events))

        if len(calendar_events) > 0:
            print("FIRST EVENT:")
            print(calendar_events[0])

        print("========================\n")

    except Exception as e:

        print("\n========================")
        print("CALENDAR ERROR")
        print("========================")
        print(str(e))
        print("========================\n")

        calendar_events = []

        from datetime import datetime

        for task in tasks:

            if task.get("status") == "Completed":
                continue

            try:

                deadline = datetime.fromisoformat(
                    task["deadline"]
                )

                if datetime.now() > deadline:
                    supabase.table("tasks").update({

                        "status": "Incomplete"

                    }).eq("id", task["id"]).execute()

                    task["status"] = "Incomplete"

            except:

                pass



    return render_template(
        "dashboard.html",
        tasks=tasks,
        calendar_events=calendar_events,
        total_tasks=total_tasks,
        completed=completed,
        pending=pending,
        productivity_score=productivity_score
    )
# ==========================================
# TASK LIST
# ==========================================

@app.route("/tasks")
def tasks():

    user_id = session["db_user"]["id"]

    response = (
        supabase
        .table("tasks")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    return render_template(
        "tasks.html",
        tasks=response.data
    )


# ==========================================
# ADD TASK PAGE
# ==========================================

@app.route("/add-task")
def add_task_page():
    return render_template("add_task.html")


# ==========================================
# SAVE TASK
# ==========================================

@app.route("/add-task", methods=["POST"])
def add_task():

    title = request.form["title"]
    description = request.form["description"]
    deadline = request.form["deadline"]

    # -------------------------
    # Gemini AI Analysis
    # -------------------------

    ai = estimate_task(

        title,

        description,

        deadline

    )

    estimated_minutes = ai["estimated_minutes"]

    priority = ai["priority"]

    difficulty = ai["difficulty"]

    reason = ai["reason"]

    # Create Google Calendar event
    event_id = create_calendar_event(
        title,
        description,
        deadline
    )

    # -------------------------
    # Save to Supabase
    # -------------------------

    user_id = session["db_user"]["id"]

    supabase.table("tasks").insert({

        "user_id": user_id,

        "title": title,
        "description": description,
        "deadline": deadline,

        "priority": priority,
        "difficulty": difficulty,
        "ai_reason": reason,
        "estimated_minutes": estimated_minutes,

        "worked_minutes": 0,
        "progress": 0,
        "timer_running": False,
        "status": "Pending",

        "google_event_id": event_id

    }).execute()

    return redirect("/tasks")


# ==========================================
# EDIT TASK PAGE
# ==========================================

@app.route("/edit-task/<int:task_id>")
def edit_task(task_id):
    user_id = session["db_user"]["id"]

    response = (
        supabase
        .table("tasks")
        .select("*")
        .eq("id", task_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        return "Task Not Found"

    return render_template(
        "edit_task.html",
        task=response.data[0]
    )


# ==========================================
# UPDATE TASK
# ==========================================

# ==========================================
# UPDATE TASK
# ==========================================

@app.route("/update-task/<int:task_id>", methods=["POST"])
def update_task(task_id):

    # Check if user is logged in
    if "db_user" not in session:
        return redirect("/")

    user_id = session["db_user"]["id"]

    title = request.form["title"]
    description = request.form["description"]
    deadline = request.form["deadline"]

    # AI recalculates estimate
    ai = estimate_task(
        title,
        description,
        deadline
    )

    (
        supabase
        .table("tasks")
        .update({

            "title": title,
            "description": description,
            "deadline": deadline,

            "priority": ai["priority"],
            "difficulty": ai["difficulty"],
            "ai_reason": ai["reason"],
            "estimated_minutes": ai["estimated_minutes"]

        })
        .eq("id", task_id)
        .eq("user_id", user_id)
        .execute()
    )

    return redirect("/tasks")



@app.route("/start-task/<int:task_id>", methods=["POST"])
def start_task(task_id):

    from datetime import datetime

    supabase.table("tasks").update({

        "status": "In Progress",

        "timer_running": True,

        "timer_started_at": datetime.now().isoformat()

    }).eq("id", task_id).execute()

    return jsonify({

        "success": True

    })


@app.route("/pause-task/<int:task_id>", methods=["POST"])
def pause_task(task_id):

    data = request.get_json()

    worked = data["worked_minutes"]

    progress = data["progress"]

    supabase.table("tasks").update({

        "worked_minutes": worked,

        "progress": progress,

        "timer_running": False

    }).eq("id", task_id).execute()

    return jsonify({

        "success": True

    })



@app.route("/finish-task/<int:task_id>", methods=["POST"])
def finish_task(task_id):

    data = request.get_json()

    worked = data["worked_minutes"]

    progress = data["progress"]

    supabase.table("tasks").update({

        "worked_minutes": worked,

        "progress": progress,

        "status": "Completed",

        "timer_running": False,

        "completed_at": datetime.datetime.now().isoformat()

    }).eq("id", task_id).execute()

    return jsonify({

        "success": True

    })


# ==========================================
# DELETE TASK
# ==========================================

@app.route("/delete-task/<int:task_id>", methods=["POST"])
def delete_task(task_id):

    # Check if user is logged in
    if "db_user" not in session:
        return redirect("/")

    user_id = session["db_user"]["id"]

    (
        supabase
        .table("tasks")
        .delete()
        .eq("id", task_id)
        .eq("user_id", user_id)
        .execute()
    )

    return redirect("/tasks")


# ==========================================
# GENERATE AI PRIORITY
# ==========================================

@app.route("/generate-priority")
def generate_priority_route():

    try:

        user_id = session["db_user"]["id"]

        tasks = (
            supabase
            .table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .execute()
            .data
        )

        for task in tasks:

            priority = generate_priority(task)

            supabase.table("tasks").update({
                "priority": priority
            }).eq("id", task["id"]).execute()

        return redirect("/tasks")

    except Exception as e:
        return str(e)


# ==========================================
# GENERATE AI PLAN
# ==========================================

@app.route("/generate-plan")
def generate_plan():
    user_id = session["db_user"]["id"]

    tasks = (
        supabase
        .table("tasks")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "Pending")
        .execute()
        .data
    )

    ai_plan = generate_schedule(tasks)

    return render_template(
        "planner.html",
        ai_plan=ai_plan
    )




# ==========================================
# GOOGLE CALENDAR
# ==========================================

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

@app.route("/calendar-events")
def calendar_events():

    service = get_calendar_service()

    # -----------------------------
    # Google Calendar Events
    # -----------------------------

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            maxResults=100,
            singleEvents=True,
            orderBy="startTime"
        )
        .execute()
    )

    google_events = events_result.get("items", [])

    # -----------------------------
    # App Tasks
    # -----------------------------

    user_id = session["db_user"]["id"]

    tasks = (
        supabase
        .table("tasks")
        .select("*")
        .eq("user_id", user_id)
        .execute()
        .data
    )

    calendar_data = []

    # =============================
    # Google Calendar Events
    # =============================

    for event in google_events:

        start = event["start"].get(
            "dateTime",
            event["start"].get("date")
        )

        calendar_data.append({

            "title": event.get("summary", "No Title"),

            "start": start,

            "color": "#9ca3af",     # Gray

            "extendedProps":{

                "priority":"GOOGLE",

                "source":"Google Calendar"

            }

        })

    # =============================
    # Tasks
    # =============================

    for task in tasks:

        priority = task.get("priority", "LOW")

        color = "#22c55e"      # Green

        if priority == "HIGH":
            color = "#ef4444"

        elif priority == "MEDIUM":
            color = "#2563eb"

        calendar_data.append({

            "title": task["title"],

            "start": task["deadline"],

            "color": color,

            "extendedProps":{

                "priority":priority,

                "description":task.get("description",""),

                "status":task.get("status","Pending"),

                "source":"Task"

            }

        })

    return jsonify(calendar_data)

@app.route("/calendar-debug")
def calendar_debug():

    service = get_calendar_service()

    calendar_list = service.calendarList().list().execute()

    return str(calendar_list)


@app.route("/all-calendars")
def all_calendars():

    service = get_calendar_service()

    calendars = service.calendarList().list().execute()

    return str(calendars)


# ===========================
# PROGRESS PAGE
# ===========================

@app.route("/progress")
def progress():
    user_id = session["db_user"]["id"]

    tasks = (
        supabase
        .table("tasks")
        .select("*")
        .eq("user_id", user_id)
        .order("deadline")
        .execute()
        .data
    )

    return render_template(
        "progress.html",
        tasks=tasks
    )



# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


@app.route("/calendar-events-debug")
def calendar_events_debug():

    service = get_calendar_service()

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            maxResults=50
        )
        .execute()
    )

    events = events_result.get("items", [])

    return {
        "total_events": len(events),
        "events": events
    }


@app.route("/future-events")
def future_events():

    events = get_upcoming_events(20)

    output = ""

    for event in events:
        output += f"""
        <h3>{event.get('summary')}</h3>
        <p>{event.get('start')}</p>
        <hr>
        """

    return output


@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/")

    email = session["user"]["email"]

    user = get_user(email)

    return render_template(
        "profile.html",
        user=user
    )

@app.route("/update-profile", methods=["POST"])
def update_profile_route():

    if "user" not in session:
        return redirect("/")

    email = session["user"]["email"]

    name = request.form["name"]
    username = request.form["username"]
    bio = request.form["bio"]
    phone = request.form["phone"]

    picture_url = None

    if "profile_picture" in request.files:

        image = request.files["profile_picture"]

        if image.filename != "":

            filename = f"{uuid.uuid4()}_{secure_filename(image.filename)}"

            image_bytes = image.read()

            supabase.storage \
                .from_("avatars") \
                .upload(
                    path=filename,
                    file=image_bytes,
                    file_options={
                        "content-type": image.content_type
                    }
                )

            picture_url = supabase.storage \
                .from_("avatars") \
                .get_public_url(filename)

    update_profile(
        email,
        name,
        username,
        bio,
        phone,
        picture_url
    )

    return redirect("/profile")


# ==========================================
# RUN APP
# ==========================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )