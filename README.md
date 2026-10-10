# Software-Laboratory-Project

```
MAPUA UNIVERSITY HELPDESK SYSTEM

How to download:
1. Click the green "Code" button, then "Download ZIP".
2. Extract the ZIP.
3. Open the extracted folder that contains app.py.

Files:
- app.py                       : Flask web application (main version)
- helpdesk_ticketing_system (2).py : command-line version
- database.py                  : SQLite database and database operations (shared)
- notifications.py             : in-app notifications (command-line version)
- reports.py                   : ticket reports and statistics (command-line version)
- attachments.py               : photo selection/storage for command-line version (uses tkinter)
- admin.py, tickets.py         : earlier standalone modules (not used by the web app)
- static/                      : logo and background images for the web app
- attachments/                 : created automatically for uploaded photos
- helpdesk.db                  : created automatically on first run
- requirements.txt             : Python dependencies

IMPORTANT:
1. Keep all .py files, static/, and requirements.txt in the same folder.
2. Open the terminal inside the folder that contains app.py
   (VS Code: File > Open Folder, then Terminal > New Terminal).

Run the web app (recommended):
1. Make sure Python 3.10+ is installed.
2. In the terminal, type pip install -r requirements.txt
3. And then type python app.py
4. Open http://127.0.0.1:5000 in your browser
5. Register a requester account on the login page.

Run the command-line version (optional):
1. Run python helpdesk_ticketing_system (2).py
2. Register a requester account through the menu.

Implemented:
- SQLite persistence for users, tickets, notifications, and ticket history
- Role-based dashboards (User, IT Staff, Admin)
- Admin ticket assignment to IT Staff
- IT Staff status updates and resolutions
- In-app notifications for ticket submission, assignment, status changes, and resolution
- Reports (Admin): total tickets, status/category/priority counts, technician workload,
  resolved/unresolved counts, and average resolution time
- Required-field and category/priority/status validation
- Optional photo attachments when creating tickets (PNG, JPG/JPEG, GIF, BMP, WEBP;
  max 5 MB in the web app). Only the requester, admin, and assigned IT staff can view them.

Important limitations:
- This is a classroom prototype. Passwords are stored as plain text and demo credentials
  are hardcoded. Do not use real passwords or deploy this version publicly.
- Notifications are stored in the app; no email/SMS delivery is implemented.
- Photo attachments are stored as local files in the attachments folder; keep this folder
  with the app and database when moving the project.
- The command-line photo picker uses tkinter and works only on a desktop; the web app
  uses the browser's file upload instead.
- Average resolution time is calculated from ticket creation to its most recent Resolved
  timestamp; reopening a ticket is not modeled as multiple resolution cycles.

```
