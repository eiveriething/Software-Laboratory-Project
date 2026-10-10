# Software-Laboratory-Project

```
MAPUA UNIVERSITY HELPDESK SYSTEM

How to download:
1. Click the green "Code" button, then "Download ZIP".
2. Extract the ZIP.
3. Open the extracted folder that contains app.py.

Files:
- app.py                       : Flask web application (main version)
- helpdesk_ticketing_system.py : command-line version
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
2. pip install -r requirements.txt
3. python app.py
4. Open http://127.0.0.1:5000 in your browser
5. Register a requester account on the login page.

Run the command-line version (optional):
1. python helpdesk_ticketing_system.py
2. Register a requester account through the menu.

(Demo credentials, Implemented, and Important limitations: keep as is.)
```
