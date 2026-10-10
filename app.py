from flask import (
    Flask, render_template_string, request,
    redirect, url_for, session, flash, abort,
    send_from_directory
)
from database import (
    initialize_database, get_user, add_user,
    create_ticket, get_tickets, get_ticket,
    get_all_users, assign_ticket, update_ticket_status,
    save_resolution, add_notification, get_notifications,
    mark_notification_read, report_summary, get_ticket_history,
)
from functools import wraps
from pathlib import Path
from werkzeug.utils import secure_filename
import random

app = Flask(__name__)
app.secret_key = "mapua-helpdesk-ticketing-system1234"

# ---------- Photo attachments (same folder/format as attachments.py) ----------
BASE_DIR = Path(__file__).resolve().parent
ATTACHMENTS_DIR = BASE_DIR / "attachments"
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload
ATTACHMENTS_DIR.mkdir(exist_ok=True)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

IT_STAFF = {
    "IT Staff 01": "it01pass",
    "IT Staff 02": "it02pass",
    "Network Support": "netpass",
    "Hardware Support": "hwpass",
}

CATEGORIES = [
    "Hardware", "Software", "Network",
    "Account/Login", "Facilities", "Other"
]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]
STATUSES = ["Assigned", "Pending", "In Progress", "Resolved", "Closed"]


# ==================================================
# SHARED DESIGN
# ==================================================

STYLE = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
      rel="stylesheet">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Karla:wght@400;500;600;700;800&display=swap"
      rel="stylesheet">
<style>
body { background:#f7f1e8; color:#263247; font-family:'Karla',Arial,sans-serif; }
.brand { color:#ad2831; font-weight:800; letter-spacing:1px; }
.btn-primary { background:#ad2831; border-color:#ad2831; }
.btn-primary:hover { background:#640d14; border-color:#640d14; }
.btn-outline-primary { color:#ad2831; border-color:#ad2831; }
.btn-outline-primary:hover { background:#ad2831; border-color:#ad2831; color:white; }
a { color:#ad2831; }
a:hover { color:#640d14; }
.text-bg-primary { background-color:#ad2831 !important; }
.bg-primary { background-color:#c9a227 !important; color:white !important; }
.prio-urgent { background-color:#6e1423; color:white; }
.prio-high   { background-color:#85182a; color:white; }
.prio-medium { background-color:#a11d33; color:white; }
.prio-low    { background-color:#a71e34; color:white; }

/* ---------- LOGIN / REGISTER (centered) ---------- */
body.auth-body {
    min-height:100vh;
    display:flex;
    align-items:center;
    justify-content:center;
    padding:24px;
    background:
        linear-gradient(rgba(59,36,24,.55), rgba(59,36,24,.55)),
        url('/static/mapua.jpg') center/cover no-repeat fixed;
}
.auth-card { width:100%; max-width:440px; padding:32px;
    background:rgba(255,255,255,.96); border-radius:16px;
    box-shadow:0 8px 28px rgba(0,0,0,.25); }
.auth-card a { font-weight:600; }
.auth-logo { width:100%; max-width:150px; height:auto; display:block; margin:0 auto 12px; }
.auth-subtitle { color:#65718a; font-weight:600; font-size:15px; }

/* ---------- SIDEBAR ---------- */
.sidebar { min-height:100vh; background:#3b2418; color:white; padding:24px 16px; }
.sidebar-logo { width:100%; max-width:150px; height:auto; display:block; margin:0 auto 8px; }
.sidebar a { display:block; color:#e1e7f5; text-decoration:none;
    padding:11px 12px; border-radius:8px; margin-top:6px; }
.sidebar a:hover { background:#5a3a28; color:white; }
.main-content { padding:30px; }
.stat-card,.content-card { background:white; border:0; border-radius:14px;
    box-shadow:0 4px 18px #1e32500d; }
.stat-number { font-size:28px; font-weight:700; }
.table th { white-space:nowrap; font-size:13px; color:#65718a; }
.table td { font-size:14px; }
@media(max-width:767px) {
    .sidebar { min-height:auto; }
    .main-content { padding:18px; }
}
</style>
"""

BASE_START = """
<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ page_title }} | Mapúa University Helpdesk</title>
""" + STYLE + """
</head><body>
<div class="container-fluid"><div class="row">
<aside class="col-md-3 col-lg-2 sidebar">
    <img src="{{ url_for('static', filename='newmapualogo.png') }}"
        alt="Mapúa University" class="sidebar-logo">
    <hr class="border-secondary">
    <div class="small text-white-50 mt-4">MAIN MENU</div>
    <a href="{{ url_for('dashboard') }}">Dashboard</a>
    {% if role == 'User' %}
        <a href="{{ url_for('create_ticket_page') }}">Create Ticket</a>
    {% endif %}
    <a href="{{ url_for('notifications_page') }}">
        Notifications{% if unread_count %} ({{ unread_count }}){% endif %}
    </a>
    {% if role == 'Admin' %}
        <a href="{{ url_for('reports_page') }}">Reports</a>
    {% endif %}
    <div class="mt-5 pt-3 border-top border-secondary">
        <div class="small text-white-50">SIGNED IN AS</div>
        <div class="fw-bold mt-1">{{ username }}</div>
        <span class="badge bg-primary mt-2">{{ role }}</span>
        <a class="mt-4" href="{{ url_for('logout') }}">Log Out</a>
    </div>
</aside>
<main class="col-md-9 col-lg-10 main-content">
{% with messages = get_flashed_messages() %}
    {% for message in messages %}
        <div class="alert alert-info">{{ message }}</div>
    {% endfor %}
{% endwith %}
"""

BASE_END = """
<p class="text-secondary small mt-4">Mapúa University Helpdesk System</p>
</main></div></div></body></html>
"""


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You do not have permission to access that page.")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def unread_notification_count(username):
    return len(get_notifications(username, unread_only=True))


def render_page(template, page_title, **context):
    username = session["username"]
    context.update({
        "page_title": page_title,
        "username": username,
        "role": session["role"],
        "unread_count": unread_notification_count(username),
    })
    return render_template_string(
        BASE_START + template + BASE_END, **context
    )


# ==================================================
# LOGIN AND REGISTRATION
# ==================================================

LOGIN_PAGE = """
<div class="auth-card">
    <div class="text-center mb-4">
        <img src="{{ url_for('static', filename='newmapualogo.png') }}"
            alt="Mapúa University" class="auth-logo">
        <div class="auth-subtitle">Mapúa University Helpdesk System</div>
        <h2 class="fw-bold mt-3">Welcome, Cardinal! &#129725;</h2>
        <p class="text-secondary">Sign in to manage your support tickets.</p>
    </div>
    {% with messages = get_flashed_messages() %}
        {% for message in messages %}<div class="alert alert-info">{{ message }}</div>{% endfor %}
    {% endwith %}
    <form method="POST">
        <label class="form-label">Username</label>
        <input class="form-control mb-3" name="username" required>
        <label class="form-label">Password</label>
        <input class="form-control mb-4" name="password" type="password" required>
        <button class="btn btn-primary w-100 py-2">Log In</button>
    </form>
    <p class="text-center mt-4 mb-0">Don't have an account?
        <a href="{{ url_for('register') }}">Register here</a>
    </p>
</div>
"""

REGISTER_PAGE = """
<div class="auth-card">
    <div class="text-center mb-4">
        <img src="{{ url_for('static', filename='newmapualogo.png') }}"
            alt="Mapúa University" class="auth-logo">
        <div class="auth-subtitle">Mapúa University Helpdesk System</div>
        <h2 class="fw-bold mt-3">Create an Account</h2>
        <p class="text-secondary">Register to submit support tickets.</p>
    </div>
    {% with messages = get_flashed_messages() %}
        {% for message in messages %}<div class="alert alert-info">{{ message }}</div>{% endfor %}
    {% endwith %}
    <form method="POST">
        <label class="form-label">Full Name</label>
        <input class="form-control mb-3" name="full_name" required>
        <label class="form-label">Username</label>
        <input class="form-control mb-3" name="username" required>
        <label class="form-label">Password</label>
        <input class="form-control mb-4" name="password" type="password" required>
        <button class="btn btn-primary w-100 py-2">Create Account</button>
    </form>
    <p class="text-center mt-4 mb-0">Already registered?
        <a href="{{ url_for('login') }}">Back to login</a>
    </p>
</div>
"""


@app.route("/", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session["username"] = username
            session["role"] = "Admin"
            return redirect(url_for("dashboard"))

        if username in IT_STAFF and IT_STAFF[username] == password:
            session.clear()
            session["username"] = username
            session["role"] = "IT Staff"
            return redirect(url_for("dashboard"))

        user = get_user(username)
        if user and user["password"] == password and user["role"] == "User":
            session.clear()
            session["username"] = username
            session["role"] = "User"
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")

    return render_template_string(
        "<!DOCTYPE html><html><head><title>Login</title>" + STYLE +
        "</head><body class='auth-body'>" + LOGIN_PAGE + "</body></html>"
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if "username" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()

        ok, message = add_user(username, password, full_name)
        flash(message)
        if ok:
            return redirect(url_for("login"))

    return render_template_string(
        "<!DOCTYPE html><html><head><title>Register</title>" + STYLE +
        "</head><body class='auth-body'>" + REGISTER_PAGE + "</body></html>"
    )


# ==================================================
# DASHBOARD
# ==================================================

DASHBOARD_CONTENT = """
<div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
    <div>
        <h2 class="fw-bold mb-1">{{ role }} Dashboard</h2>
        <p class="text-secondary mb-0">Welcome back, {{ username }}!</p>
    </div>
    {% if role == 'User' %}
        <a class="btn btn-primary" href="{{ url_for('create_ticket_page') }}">+ Create Ticket</a>
    {% endif %}
</div>

<div class="row g-3 mb-4">
    {% for label, number, note in [
        ('Tickets', total_tickets, 'Tickets in your view'),
        ('Open', open_tickets, 'Awaiting action'),
        ('In Progress', in_progress_tickets, 'Currently being handled'),
        ('Resolved', resolved_tickets, 'Resolved or closed')
    ] %}
    <div class="col-sm-6 col-xl-3">
        <div class="card stat-card p-3 h-100">
            <div class="text-secondary small">{{ label }}</div>
            <div class="stat-number mt-2">{{ number }}</div>
            <div class="small text-secondary">{{ note }}</div>
        </div>
    </div>
    {% endfor %}
</div>

<div class="card content-card p-4" id="tickets">
    <div class="mb-3">
        <h5 class="fw-bold mb-1">Ticket Overview</h5>
        <p class="text-secondary small mb-0">
            {% if role == 'Admin' %}View and assign all submitted tickets.
            {% elif role == 'IT Staff' %}View tickets assigned to you.
            {% else %}View tickets you have submitted.{% endif %}
        </p>
    </div>
    <div class="table-responsive">
    <table class="table table-hover align-middle">
        <thead class="table-light"><tr>
            <th>Ticket ID</th><th>Subject</th><th>Category</th>
            <th>Priority</th><th>Status</th>
            {% if role == 'Admin' %}<th>Submitted By</th><th>Assigned To</th>{% endif %}
            <th>Action</th>
        </tr></thead>
        <tbody>
        {% for ticket in tickets %}
        <tr>
            <td class="fw-bold">{{ ticket['ticket_id'] }}</td>
            <td>{{ ticket['title'] }}</td>
            <td>{{ ticket['category'] }}</td>
            <td>
                <span class="badge
                {% if ticket['priority'] == 'Urgent' %}prio-urgent
                {% elif ticket['priority'] == 'High' %}prio-high
                {% elif ticket['priority'] == 'Medium' %}prio-medium
                {% else %}prio-low{% endif %}">
                {{ ticket['priority'] }}</span>
            </td>
            <td><span class="badge
                {% if ticket['status'] in ('Resolved','Closed') %}text-bg-success
                {% elif ticket['status'] == 'In Progress' %}text-bg-primary
                {% elif ticket['status'] == 'Pending' %}text-bg-warning
                {% else %}text-bg-light border text-dark{% endif %}">
                {{ ticket['status'] }}</span>
            </td>
            {% if role == 'Admin' %}
                <td>{{ ticket['username'] }}</td>
                <td>{{ ticket['assigned_to'] or 'Unassigned' }}</td>
            {% endif %}
            <td><a class="btn btn-sm btn-outline-primary"
                href="{{ url_for('ticket_detail', ticket_id=ticket['ticket_id']) }}">View</a></td>
        </tr>
        {% else %}
        <tr><td colspan="8" class="text-center text-secondary py-5">
            No tickets found.
        </td></tr>
        {% endfor %}
        </tbody>
    </table>
    </div>
</div>
"""


@app.route("/dashboard")
@login_required
def dashboard():
    username, role = session["username"], session["role"]

    if role == "Admin":
        tickets = get_tickets()
    elif role == "IT Staff":
        tickets = get_tickets(assigned_to=username)
    else:
        tickets = get_tickets(username=username)

    return render_page(
        DASHBOARD_CONTENT, "Dashboard",
        tickets=tickets,
        total_tickets=len(tickets),
        open_tickets=sum(t["status"] == "Open" for t in tickets),
        in_progress_tickets=sum(t["status"] == "In Progress" for t in tickets),
        resolved_tickets=sum(t["status"] in ("Resolved", "Closed") for t in tickets),
    )


# ==================================================
# CREATE TICKET
# ==================================================

CREATE_TICKET_CONTENT = """
<div class="mb-3">
    <a class="text-decoration-none" href="{{ url_for('dashboard') }}">&larr; Back to Dashboard</a>
</div>
<div class="card content-card p-4" style="max-width:760px">
    <div class="brand mb-2">HELPDESK</div>
    <h2 class="fw-bold">Create a Support Ticket</h2>
    <p class="text-secondary">Tell us about the issue you need help with.</p>
    <form method="POST" enctype="multipart/form-data">
        <label class="form-label">Issue Title</label>
        <input class="form-control mb-3" name="title" maxlength="150" required>
        <label class="form-label">Description</label>
        <textarea class="form-control mb-3" name="description" rows="5" required></textarea>
        <label class="form-label">Category</label>
        <select class="form-select mb-3" name="category" required>
            {% for item in categories %}<option>{{ item }}</option>{% endfor %}
        </select>
        <label class="form-label">Priority</label>
        <select class="form-select mb-3" name="priority" required>
            {% for item in priorities %}
            <option {% if item == 'Medium' %}selected{% endif %}>{{ item }}</option>
            {% endfor %}
        </select>
        <label class="form-label">Photo Attachment (optional)</label>
        <input class="form-control mb-1" type="file" name="photo" accept="image/*">
        <div class="form-text mb-4">PNG, JPG, GIF, BMP, or WEBP. Maximum 5 MB.</div>
        <button class="btn btn-primary">Submit Ticket</button>
        <a class="btn btn-outline-secondary" href="{{ url_for('dashboard') }}">Cancel</a>
    </form>
</div>
"""


@app.route("/tickets/new", methods=["GET", "POST"])
@role_required("User")
def create_ticket_page():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        priority = request.form.get("priority", "")

        photo = request.files.get("photo")
        has_photo = bool(photo and photo.filename)
        photo_ext = (
            Path(secure_filename(photo.filename)).suffix.lower()
            if has_photo else ""
        )

        if not title or not description:
            flash("Please complete all required fields.")
        elif len(title) > 150:
            flash("The issue title must be 150 characters or fewer.")
        elif category not in CATEGORIES or priority not in PRIORITIES:
            flash("Please select a valid category and priority.")
        elif has_photo and photo_ext not in ALLOWED_EXT:
            flash("Only image files (png, jpg, jpeg, gif, bmp, webp) are allowed.")
        else:
            ticket_id = None
            for _ in range(100):
                candidate = f"TCK-{random.randint(0, 99999):05d}"
                if get_ticket(candidate) is None:
                    ticket_id = candidate
                    break

            if ticket_id is None:
                flash("Unable to generate a ticket ID. Please try again.")
            else:
                try:
                    photo_path = None
                    if has_photo:
                        destination = ATTACHMENTS_DIR / f"{ticket_id}{photo_ext}"
                        photo.save(destination)
                        photo_path = destination.relative_to(BASE_DIR).as_posix()

                    create_ticket(
                        ticket_id, title, description, category,
                        priority, session["username"], photo_path
                    )
                    add_notification(
                        session["username"],
                        f"Your ticket {ticket_id} was created successfully.",
                        ticket_id,
                    )
                    flash(f"Ticket {ticket_id} created successfully!")
                    return redirect(url_for("dashboard"))
                except Exception:
                    app.logger.exception("Unable to create ticket")
                    flash("Something went wrong while creating the ticket.")

    return render_page(
        CREATE_TICKET_CONTENT, "Create Ticket",
        categories=CATEGORIES, priorities=PRIORITIES
    )


# ==================================================
# TICKET DETAILS + ADMIN ASSIGNMENT + STAFF ACTIONS
# ==================================================

TICKET_DETAIL_CONTENT = """
<div class="mb-3">
    <a class="text-decoration-none" href="{{ url_for('dashboard') }}">&larr; Back to Dashboard</a>
</div>

<div class="card content-card p-4 mb-4">
    <div class="d-flex flex-wrap justify-content-between gap-2">
        <div>
            <div class="text-secondary small">{{ ticket['ticket_id'] }}</div>
            <h2 class="fw-bold mt-1">{{ ticket['title'] }}</h2>
        </div>
        <span class="badge text-bg-primary align-self-start">{{ ticket['status'] }}</span>
    </div>
    <hr>
    <div class="row g-3">
        <div class="col-md-6"><strong>Submitted by</strong><div>{{ ticket['username'] }}</div></div>
        <div class="col-md-6"><strong>Assigned to</strong><div>{{ ticket['assigned_to'] or 'Unassigned' }}</div></div>
        <div class="col-md-6"><strong>Category</strong><div>{{ ticket['category'] }}</div></div>
        <div class="col-md-6"><strong>Priority</strong><div>{{ ticket['priority'] }}</div></div>
        <div class="col-md-6"><strong>Created</strong><div>{{ ticket['created_at'] }}</div></div>
        <div class="col-md-6"><strong>Last updated</strong><div>{{ ticket['updated_at'] }}</div></div>
    </div>
    <hr>
    <h6 class="fw-bold">Description</h6>
    <p style="white-space:pre-wrap">{{ ticket['description'] }}</p>
    {% if ticket['photo_path'] %}
    <h6 class="fw-bold mt-3">Photo Attachment</h6>
    <a href="{{ url_for('ticket_photo', ticket_id=ticket['ticket_id']) }}" target="_blank">
        <img src="{{ url_for('ticket_photo', ticket_id=ticket['ticket_id']) }}"
             class="img-fluid rounded border" style="max-height:300px" alt="Ticket attachment">
    </a>
    {% endif %}
    <h6 class="fw-bold mt-3">Resolution</h6>
    <p style="white-space:pre-wrap">{{ ticket['resolution'] or 'No resolution recorded yet.' }}</p>
</div>

{% if role == 'Admin' %}
<div class="card content-card p-4 mb-4">
    <h5 class="fw-bold">Assign Ticket to IT Staff</h5>
    <form method="POST" action="{{ url_for('assign_ticket_route', ticket_id=ticket['ticket_id']) }}">
        <label class="form-label">Select staff member</label>
        <select class="form-select mb-3" name="assigned_to" required>
            <option value="">Choose IT Staff</option>
            {% for staff in staff_members %}
            <option value="{{ staff }}" {% if ticket['assigned_to'] == staff %}selected{% endif %}>
                {{ staff }}
            </option>
            {% endfor %}
        </select>
        <button class="btn btn-primary">Assign Ticket</button>
    </form>
</div>
{% endif %}

{% if role == 'IT Staff' and ticket['assigned_to'] == username and ticket['status'] not in ('Resolved','Closed','Cancelled') %}
<div class="card content-card p-4 mb-4">
    <h5 class="fw-bold">Update Ticket Status</h5>
    <form method="POST" action="{{ url_for('update_status_route', ticket_id=ticket['ticket_id']) }}">
        <label class="form-label">New status</label>
        <select class="form-select mb-3" name="status" required>
            {% for status in statuses %}
            <option value="{{ status }}" {% if ticket['status'] == status %}selected{% endif %}>
                {{ status }}
            </option>
            {% endfor %}
        </select>
        <button class="btn btn-primary">Update Status</button>
    </form>
    <hr>
    <h5 class="fw-bold">Save Resolution</h5>
    <form method="POST" action="{{ url_for('resolve_ticket_route', ticket_id=ticket['ticket_id']) }}">
        <label class="form-label">Resolution details</label>
        <textarea class="form-control mb-3" name="resolution" rows="4"
                  placeholder="Describe the troubleshooting steps and solution" required></textarea>
        <button class="btn btn-success">Save Resolution</button>
    </form>
</div>
{% endif %}

<div class="card content-card p-4">
    <h5 class="fw-bold">Ticket History</h5>
    <div class="table-responsive">
    <table class="table align-middle">
        <thead><tr><th>Date</th><th>Action</th><th>By</th><th>Details</th></tr></thead>
        <tbody>
        {% for item in history %}
        <tr>
            <td>{{ item['created_at'] }}</td>
            <td>{{ item['action'] }}
                {% if item['old_status'] or item['new_status'] %}
                <div class="small text-secondary">{{ item['old_status'] or '—' }} → {{ item['new_status'] or '—' }}</div>
                {% endif %}
            </td>
            <td>{{ item['actor'] }}</td>
            <td>{{ item['details'] or '—' }}</td>
        </tr>
        {% else %}
        <tr><td colspan="4" class="text-secondary">No history available.</td></tr>
        {% endfor %}
        </tbody>
    </table>
    </div>
</div>
"""


def user_can_view_ticket(ticket):
    role, username = session["role"], session["username"]
    if role == "Admin":
        return True
    if role == "IT Staff":
        return ticket["assigned_to"] == username
    return ticket["username"] == username


@app.route("/tickets/<ticket_id>")
@login_required
def ticket_detail(ticket_id):
    ticket = get_ticket(ticket_id)
    if not ticket:
        abort(404)
    if not user_can_view_ticket(ticket):
        flash("You do not have permission to view that ticket.")
        return redirect(url_for("dashboard"))

    return render_page(
        TICKET_DETAIL_CONTENT, "Ticket Details",
        ticket=ticket,
        staff_members=list(IT_STAFF.keys()),
        statuses=STATUSES,
        history=get_ticket_history(ticket_id),
    )


@app.route("/tickets/<ticket_id>/photo")
@login_required
def ticket_photo(ticket_id):
    ticket = get_ticket(ticket_id)
    if not ticket or not ticket["photo_path"] or not user_can_view_ticket(ticket):
        abort(404)
    # Path(...).name keeps only the filename so nothing outside attachments/ is served.
    return send_from_directory(ATTACHMENTS_DIR, Path(ticket["photo_path"]).name)


@app.route("/tickets/<ticket_id>/assign", methods=["POST"])
@role_required("Admin")
def assign_ticket_route(ticket_id):
    ticket = get_ticket(ticket_id)

    if not ticket:
        flash("Ticket not found.")
        return redirect(url_for("dashboard"))

    assigned_to = request.form.get("assigned_to", "").strip()

    if assigned_to not in IT_STAFF:
        flash("Please select a valid IT Staff member.")
        return redirect(
            url_for("ticket_detail", ticket_id=ticket_id)
        )

    try:
        ok, message = assign_ticket(
            ticket_id, assigned_to, session["username"]
        )

        if not ok:
            flash(message)
            return redirect(
                url_for("ticket_detail", ticket_id=ticket_id)
            )

        updated_ticket = get_ticket(ticket_id)

        if not updated_ticket or updated_ticket["assigned_to"] != assigned_to:
            flash("Assignment was not saved. Please try again.")
            return redirect(
                url_for("ticket_detail", ticket_id=ticket_id)
            )

        add_notification(
            assigned_to,
            f"Ticket {ticket_id} has been assigned to you.",
            ticket_id,
        )

        add_notification(
            ticket["username"],
            f"Your ticket {ticket_id} has been assigned to {assigned_to}.",
            ticket_id,
        )

        flash(
            f"Ticket {ticket_id} successfully assigned to {assigned_to}!"
        )

    except Exception:
        app.logger.exception("Ticket assignment failed.")
        flash("An error occurred while assigning the ticket.")

    return redirect(
        url_for("ticket_detail", ticket_id=ticket_id)
    )


@app.route("/tickets/<ticket_id>/status", methods=["POST"])
@role_required("IT Staff")
def update_status_route(ticket_id):
    ticket = get_ticket(ticket_id)
    if not ticket:
        abort(404)
    if ticket["assigned_to"] != session["username"]:
        flash("You can only update tickets assigned to you.")
        return redirect(url_for("dashboard"))

    new_status = request.form.get("status", "")
    if new_status not in STATUSES:
        flash("Please select a valid status.")
        return redirect(url_for("ticket_detail", ticket_id=ticket_id))

    ok, message = update_ticket_status(
        ticket_id, new_status, session["username"]
    )
    flash(message)
    if ok:
        add_notification(
            ticket["username"],
            f"Ticket {ticket_id} status updated to {new_status}.",
            ticket_id,
        )
    return redirect(url_for("ticket_detail", ticket_id=ticket_id))


@app.route("/tickets/<ticket_id>/resolve", methods=["POST"])
@role_required("IT Staff")
def resolve_ticket_route(ticket_id):
    ticket = get_ticket(ticket_id)
    if not ticket:
        abort(404)
    if ticket["assigned_to"] != session["username"]:
        flash("You can only resolve tickets assigned to you.")
        return redirect(url_for("dashboard"))

    resolution = request.form.get("resolution", "").strip()
    if not resolution:
        flash("Please enter the resolution details.")
        return redirect(url_for("ticket_detail", ticket_id=ticket_id))

    ok, message = save_resolution(
        ticket_id, resolution, session["username"]
    )
    flash(message)
    if ok:
        add_notification(
            ticket["username"],
            f"Ticket {ticket_id} has been resolved.",
            ticket_id,
        )
    return redirect(url_for("ticket_detail", ticket_id=ticket_id))


# ==================================================
# NOTIFICATIONS
# ==================================================

NOTIFICATIONS_CONTENT = """
<div class="mb-4">
    <h2 class="fw-bold">Notifications</h2>
    <p class="text-secondary">Updates about your tickets and assignments.</p>
</div>
<div class="card content-card p-4">
    {% for item in notifications %}
    <div class="d-flex justify-content-between align-items-start gap-3 border-bottom py-3">
        <div>
            {% if not item['is_read'] %}<span class="badge text-bg-primary">New</span>{% endif %}
            <div class="mt-1">{{ item['message'] }}</div>
            <small class="text-secondary">{{ item['created_at'] }}</small>
            {% if item['ticket_id'] %}
            <div><a href="{{ url_for('ticket_detail', ticket_id=item['ticket_id']) }}">View ticket</a></div>
            {% endif %}
        </div>
        {% if not item['is_read'] %}
        <form method="POST" action="{{ url_for('read_notification', notification_id=item['notification_id']) }}">
            <button class="btn btn-sm btn-outline-secondary">Mark read</button>
        </form>
        {% endif %}
    </div>
    {% else %}
        <p class="text-secondary mb-0">You don't have any notifications yet.</p>
    {% endfor %}
</div>
"""


@app.route("/notifications")
@login_required
def notifications_page():
    return render_page(
        NOTIFICATIONS_CONTENT, "Notifications",
        notifications=get_notifications(session["username"])
    )


@app.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def read_notification(notification_id):
    mark_notification_read(notification_id, session["username"])
    flash("Notification marked as read.")
    return redirect(url_for("notifications_page"))


# ==================================================
# REPORTS (ADMIN ONLY)
# ==================================================

REPORTS_CONTENT = """
<div class="mb-4">
    <h2 class="fw-bold">Reports</h2>
    <p class="text-secondary">Overview of helpdesk ticket activity.</p>
</div>

<div class="row g-3 mb-4">
    <div class="col-sm-6 col-xl-3"><div class="card stat-card p-3">
        <div class="text-secondary small">Total Tickets</div>
        <div class="stat-number">{{ summary['total'] }}</div>
    </div></div>
    <div class="col-sm-6 col-xl-3"><div class="card stat-card p-3">
        <div class="text-secondary small">Resolved / Closed</div>
        <div class="stat-number">{{ summary['resolved_count'] }}</div>
    </div></div>
    <div class="col-sm-6 col-xl-3"><div class="card stat-card p-3">
        <div class="text-secondary small">Unresolved</div>
        <div class="stat-number">{{ summary['unresolved_count'] }}</div>
    </div></div>
    <div class="col-sm-6 col-xl-3"><div class="card stat-card p-3">
        <div class="text-secondary small">Average Resolution Time</div>
        <div class="stat-number">
        {% if summary['average_resolution_hours'] is not none %}
            {{ "%.1f"|format(summary['average_resolution_hours']) }} h
        {% else %}—{% endif %}
        </div>
    </div></div>
</div>

<div class="row g-4">
    {% for heading, rows, key in [
        ('Tickets by Status', summary['by_status'], 'status'),
        ('Tickets by Category', summary['by_category'], 'category'),
        ('Tickets by Priority', summary['by_priority'], 'priority'),
        ('Tickets by Staff Workload', summary['workload'], 'technician')
    ] %}
    <div class="col-lg-6">
        <div class="card content-card p-4 h-100">
            <h5 class="fw-bold mb-3">{{ heading }}</h5>
            <div class="table-responsive">
            <table class="table">
                <thead><tr><th>{{ heading }}</th><th class="text-end">Count</th></tr></thead>
                <tbody>
                {% for row in rows %}
                <tr><td>{{ row[key] }}</td><td class="text-end">{{ row['total'] }}</td></tr>
                {% else %}
                <tr><td colspan="2" class="text-secondary">No data available.</td></tr>
                {% endfor %}
                </tbody>
            </table>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
"""


@app.route("/reports")
@role_required("Admin")
def reports_page():
    return render_page(
        REPORTS_CONTENT, "Reports",
        summary=report_summary()
    )


# ==================================================
# LOGOUT AND START
# ==================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.errorhandler(413)
def file_too_large(error):
    flash("That file is too large. Maximum size is 5 MB.")
    if session.get("role") == "User":
        return redirect(url_for("create_ticket_page"))
    return redirect(url_for("login"))


@app.errorhandler(404)
def not_found(error):
    return render_template_string(
        "<!DOCTYPE html><html><head><title>Not Found</title>" + STYLE +
        "</head><body><div class='container py-5'><h2>Ticket not found</h2>"
        "<a href='/dashboard'>Return to dashboard</a></div></body></html>"
    ), 404


if __name__ == "__main__":
    initialize_database()
    app.run(debug=False, use_reloader=False)