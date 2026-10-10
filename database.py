import sqlite3
from datetime import datetime

DB_NAME = "helpdesk.db"


def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create the tables if they do not already exist."""
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'User'
        );

        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            username TEXT NOT NULL,
            assigned_to TEXT,
            resolution TEXT,
            photo_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            resolved_at TEXT
        );

        CREATE TABLE IF NOT EXISTS notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            ticket_id TEXT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS ticket_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT,
            details TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id)
                ON DELETE CASCADE
        );
        """)

        # Migration: add photo_path to an older helpdesk.db that doesn't have it yet.
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(tickets)")]
        if "photo_path" not in columns:
            conn.execute("ALTER TABLE tickets ADD COLUMN photo_path TEXT")


def add_user(username, password, full_name, role="User"):
    username = username.strip()
    full_name = full_name.strip()
    if not username or not password or not full_name:
        return False, "Username, password, and full name are required."

    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                (username, password, full_name, role)
            )
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "That username is already taken."


def get_user(username):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()


def get_all_users(role=None):
    with get_connection() as conn:
        if role:
            return conn.execute(
                "SELECT * FROM users WHERE role = ? ORDER BY username", (role,)
            ).fetchall()
        return conn.execute("SELECT * FROM users ORDER BY username").fetchall()


def create_ticket(ticket_id, title, description, category, priority,
                  username, photo_path=None):
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO tickets
            (ticket_id, title, description, category, priority, status,
             username, photo_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'Open', ?, ?, ?, ?)
        """, (ticket_id, title, description, category, priority,
              username, photo_path, now, now))
        conn.execute("""
            INSERT INTO ticket_history
            (ticket_id, actor, action, old_status, new_status, details, created_at)
            VALUES (?, ?, 'Ticket created', NULL, 'Open', ?, ?)
        """, (ticket_id, username, title, now))


def get_tickets(username=None, assigned_to=None):
    sql = "SELECT * FROM tickets"
    conditions, values = [], []
    if username is not None:
        conditions.append("username = ?")
        values.append(username)
    if assigned_to is not None:
        conditions.append("assigned_to = ?")
        values.append(assigned_to)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY created_at DESC"
    with get_connection() as conn:
        return conn.execute(sql, values).fetchall()


def get_ticket(ticket_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM tickets WHERE ticket_id = ?", (str(ticket_id).strip(),)
        ).fetchone()


def search_tickets(term):
    term = f"%{term.strip()}%"
    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM tickets
            WHERE ticket_id LIKE ? OR title LIKE ? OR username LIKE ?
               OR category LIKE ? OR status LIKE ?
            ORDER BY created_at DESC
        """, (term, term, term, term, term)).fetchall()


def assign_ticket(ticket_id, assigned_to, actor="admin"):
    ticket = get_ticket(ticket_id)
    if not ticket:
        return False, "Ticket not found."
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute("""
            UPDATE tickets SET assigned_to = ?, status = 'Assigned', updated_at = ?
            WHERE ticket_id = ?
        """, (assigned_to, now, ticket_id))
        conn.execute("""
            INSERT INTO ticket_history
            (ticket_id, actor, action, old_status, new_status, details, created_at)
            VALUES (?, ?, 'Ticket assigned', ?, 'Assigned', ?, ?)
        """, (ticket_id, actor, ticket["status"], assigned_to, now))
    return True, f"Ticket {ticket_id} assigned to {assigned_to}."


def update_ticket_status(ticket_id, new_status, actor):
    allowed = {"Open", "Assigned", "Pending", "In Progress", "Resolved", "Closed", "Cancelled"}
    if new_status not in allowed:
        return False, "Invalid status."
    ticket = get_ticket(ticket_id)
    if not ticket:
        return False, "Ticket not found."
    now = datetime.now().isoformat(timespec="seconds")
    resolved_at = now if new_status == "Resolved" else ticket["resolved_at"]
    with get_connection() as conn:
        conn.execute("""
            UPDATE tickets
            SET status = ?, updated_at = ?, resolved_at = ?
            WHERE ticket_id = ?
        """, (new_status, now, resolved_at, ticket_id))
        conn.execute("""
            INSERT INTO ticket_history
            (ticket_id, actor, action, old_status, new_status, details, created_at)
            VALUES (?, ?, 'Status updated', ?, ?, NULL, ?)
        """, (ticket_id, actor, ticket["status"], new_status, now))
    return True, f"Ticket status changed to {new_status}."


def save_resolution(ticket_id, resolution, actor):
    if not resolution.strip():
        return False, "Resolution details cannot be empty."
    ticket = get_ticket(ticket_id)
    if not ticket:
        return False, "Ticket not found."
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute("""
            UPDATE tickets SET resolution = ?, status = 'Resolved',
                updated_at = ?, resolved_at = ? WHERE ticket_id = ?
        """, (resolution.strip(), now, now, ticket_id))
        conn.execute("""
            INSERT INTO ticket_history
            (ticket_id, actor, action, old_status, new_status, details, created_at)
            VALUES (?, ?, 'Resolution added', ?, 'Resolved', ?, ?)
        """, (ticket_id, actor, ticket["status"], resolution.strip(), now))
    return True, "Resolution saved and ticket marked Resolved."


def add_notification(username, message, ticket_id=None):
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO notifications (username, ticket_id, message, created_at)
            VALUES (?, ?, ?, ?)
        """, (username, ticket_id, message, now))


def get_notifications(username, unread_only=False):
    sql = "SELECT * FROM notifications WHERE username = ?"
    values = [username]
    if unread_only:
        sql += " AND is_read = 0"
    sql += " ORDER BY created_at DESC"
    with get_connection() as conn:
        return conn.execute(sql, values).fetchall()


def mark_notification_read(notification_id, username):
    with get_connection() as conn:
        conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE notification_id = ? AND username = ?",
            (notification_id, username)
        )


def report_summary():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM tickets").fetchone()["n"]
        by_status = conn.execute("""
            SELECT status, COUNT(*) AS total FROM tickets
            GROUP BY status ORDER BY status
        """).fetchall()
        by_category = conn.execute("""
            SELECT category, COUNT(*) AS total FROM tickets
            GROUP BY category ORDER BY category
        """).fetchall()
        by_priority = conn.execute("""
            SELECT priority, COUNT(*) AS total FROM tickets
            GROUP BY priority ORDER BY priority
        """).fetchall()
        workload = conn.execute("""
            SELECT COALESCE(assigned_to, 'Unassigned') AS technician,
                   COUNT(*) AS total
            FROM tickets GROUP BY assigned_to ORDER BY total DESC
        """).fetchall()
        resolved = conn.execute("""
            SELECT created_at, resolved_at FROM tickets
            WHERE resolved_at IS NOT NULL AND status IN ('Resolved', 'Closed')
        """).fetchall()

    durations = []
    for row in resolved:
        try:
            start = datetime.fromisoformat(row["created_at"])
            end = datetime.fromisoformat(row["resolved_at"])
            durations.append((end - start).total_seconds() / 3600)
        except (TypeError, ValueError):
            pass
    average_hours = sum(durations) / len(durations) if durations else None
    return {
        "total": total,
        "by_status": by_status,
        "by_category": by_category,
        "by_priority": by_priority,
        "workload": workload,
        "average_resolution_hours": average_hours,
        "resolved_count": len(durations),
        "unresolved_count": total - len(durations)
    }


def get_ticket_history(ticket_id):
    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM ticket_history WHERE ticket_id = ?
            ORDER BY created_at
        """, (ticket_id,)).fetchall()