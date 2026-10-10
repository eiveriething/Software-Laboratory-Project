import random
from database import (
    initialize_database, add_user, get_user, get_all_users, create_ticket,
    get_tickets, get_ticket, search_tickets, assign_ticket,
    update_ticket_status, save_resolution
)
from notifications import notify_user, show_notifications
from reports import show_reports

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

IT_STAFF = {
    "IT Staff 01": "it01pass",
    "IT Staff 02": "it02pass",
    "Network Support": "netpass",
    "Hardware Support": "hwpass",
}

STATUSES = ["Open", "Assigned", "Pending", "In Progress", "Resolved", "Closed", "Cancelled"]
CATEGORIES = ["Hardware", "Software", "Network", "Account/Login", "Facilities", "Other"]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]


def generate_ticket_id():
    # Database primary key prevents duplicate IDs; retry if a collision occurs.
    return f"TCK-{random.randint(10000, 99999)}"


def print_ticket(ticket):
    print("\n------------------------------")
    for label, field in [
        ("Ticket ID", "ticket_id"), ("Title", "title"),
        ("Description", "description"), ("Category", "category"),
        ("Priority", "priority"), ("Status", "status"),
        ("Requester", "username"), ("Assigned To", "assigned_to"),
        ("Resolution", "resolution"), ("Created At", "created_at"),
        ("Updated At", "updated_at")
    ]:
        value = ticket[field]
        if field == "assigned_to" and not value:
            value = "Not assigned"
        if field == "resolution" and not value:
            value = "Pending"
        print(f"{label}: {value}")


def create_new_ticket(username):
    print("\n====== CREATE TICKET ======")
    title = input("Title: ").strip()
    description = input("Describe the issue: ").strip()
    print("Categories:", ", ".join(CATEGORIES))
    category = input("Category: ").strip()
    print("Priorities:", ", ".join(PRIORITIES))
    priority = input("Priority: ").strip().title()

    if not title or not description:
        print("Title and description are required.")
        return
    if category.lower() not in [x.lower() for x in CATEGORIES]:
        print("Invalid category. Please choose one from the list.")
        return
    category = next(x for x in CATEGORIES if x.lower() == category.lower())
    if priority.lower() not in [x.lower() for x in PRIORITIES]:
        print("Invalid priority. Please choose Low, Medium, High, or Urgent.")
        return
    priority = next(x for x in PRIORITIES if x.lower() == priority.lower())

    while True:
        ticket_id = generate_ticket_id()
        if not get_ticket(ticket_id):
            break
    create_ticket(ticket_id, title, description, category, priority, username)
    notify_user(username, ticket_id, "Your ticket has been submitted successfully.")
    print(f"\nTicket created successfully. Your ticket ID is {ticket_id}.")


def view_tickets(rows):
    if not rows:
        print("\nNo tickets found.")
        return
    for ticket in rows:
        print_ticket(ticket)


def requester_menu(username):
    while True:
        print(f"\n====== USER MENU ({username}) ======")
        print("1. Create Ticket")
        print("2. View My Tickets")
        print("3. Notifications")
        print("4. Logout")
        choice = input("Enter choice: ").strip()
        if choice == "1":
            create_new_ticket(username)
        elif choice == "2":
            view_tickets(get_tickets(username=username))
        elif choice == "3":
            show_notifications(username)
        elif choice == "4":
            break
        else:
            print("Invalid choice.")


def admin_menu():
    while True:
        print("\n====== ADMIN DASHBOARD ======")
        print("1. View All Tickets")
        print("2. Search Tickets")
        print("3. Assign Ticket")
        print("4. Reports")
        print("5. Logout")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            view_tickets(get_tickets())
        elif choice == "2":
            term = input("Search by ID, title, requester, category, or status: ").strip()
            view_tickets(search_tickets(term))
        elif choice == "3":
            ticket_id = input("Ticket ID: ").strip()
            ticket = get_ticket(ticket_id)
            if not ticket:
                print("Ticket not found.")
                continue
            print("Available staff:")
            for staff_name in IT_STAFF:
                print(f"- {staff_name}")
            assigned_to = input("Enter exact staff name: ").strip()
            if assigned_to not in IT_STAFF:
                print("Invalid staff name.")
                continue
            ok, message = assign_ticket(ticket_id, assigned_to)
            print(message)
            if ok:
                notify_user(ticket["username"], ticket_id, f"Your ticket has been assigned to {assigned_to}.")
                notify_user(assigned_to, ticket_id, "A ticket has been assigned to you.")
        elif choice == "4":
            show_reports()
        elif choice == "5":
            break
        else:
            print("Invalid choice.")


def it_menu(username):
    while True:
        assigned = get_tickets(assigned_to=username)
        print(f"\n====== IT DASHBOARD ({username}) ======")
        print("1. View My Assigned Tickets")
        print("2. Search My Assigned Tickets")
        print("3. Update Ticket Status")
        print("4. Add Resolution")
        print("5. Notifications")
        print("6. Logout")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            view_tickets(assigned)
        elif choice == "2":
            term = input("Enter ticket ID or search term: ").strip().lower()
            matches = [t for t in assigned if term in str(t["ticket_id"]).lower()
                       or term in t["title"].lower()]
            view_tickets(matches)
        elif choice == "3":
            ticket_id = input("Ticket ID: ").strip()
            ticket = get_ticket(ticket_id)
            if not ticket or ticket["assigned_to"] != username:
                print("Ticket not found among your assigned tickets.")
                continue
            print("Statuses:", ", ".join(STATUSES))
            status = input("New status: ").strip().title()
            if status not in STATUSES:
                print("Invalid status.")
                continue
            ok, message = update_ticket_status(ticket_id, status, username)
            print(message)
            if ok:
                notify_user(ticket["username"], ticket_id, f"Status updated to {status}.")
        elif choice == "4":
            ticket_id = input("Ticket ID: ").strip()
            ticket = get_ticket(ticket_id)
            if not ticket or ticket["assigned_to"] != username:
                print("Ticket not found among your assigned tickets.")
                continue
            resolution = input("Resolution details: ").strip()
            ok, message = save_resolution(ticket_id, resolution, username)
            print(message)
            if ok:
                notify_user(ticket["username"], ticket_id, "A resolution has been recorded and the ticket is marked Resolved.")
        elif choice == "5":
            show_notifications(username)
        elif choice == "6":
            break
        else:
            print("Invalid choice.")


def login_gate():
    while True:
        print("\n================================")
        print("   HELP DESK TICKETING SYSTEM")
        print("================================")
        print("1. Admin Login")
        print("2. IT Staff Login")
        print("3. User Login")
        print("4. Register User")
        print("5. Exit")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            username = input("Admin username: ").strip()
            password = input("Admin password: ").strip()
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                admin_menu()
            else:
                print("Invalid admin credentials.")
        elif choice == "2":
            username = input("IT staff username (exact name): ").strip()
            password = input("Password: ").strip()
            if username in IT_STAFF and IT_STAFF[username] == password:
                it_menu(username)
            else:
                print("Invalid IT staff credentials.")
        elif choice == "3":
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            user = get_user(username)
            if user and user["password"] == password and user["role"] == "User":
                requester_menu(username)
            else:
                print("Invalid user credentials.")
        elif choice == "4":
            username = input("Choose a username: ").strip()
            password = input("Choose a password: ").strip()
            full_name = input("Full name: ").strip()
            ok, message = add_user(username, password, full_name)
            print(message)
        elif choice == "5":
            print("Goodbye!")
            return
        else:
            print("Invalid choice.")


def main():
    initialize_database()
    login_gate()


if __name__ == "__main__":
    main()
