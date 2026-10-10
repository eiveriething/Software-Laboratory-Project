"""Photo attachment helpers for the Helpdesk Ticketing System."""
from pathlib import Path
import shutil
import webbrowser
import tkinter as tk
from tkinter import filedialog

BASE_DIR = Path(__file__).resolve().parent
ATTACHMENTS_DIR = BASE_DIR / "attachments"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def attach_photo(ticket_id):
    """Prompt the user to choose an image and copy it into the attachments folder.

    Returns a project-relative path, or None if the user skips/cancels.
    """
    root = tk.Tk()
    root.withdraw()
    try:
        selected = filedialog.askopenfilename(
            parent=root,
            title=f"Attach a photo to {ticket_id}",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp")],
        )
    finally:
        root.destroy()

    if not selected:
        print("No photo attached.")
        return None

    source = Path(selected)
    if source.suffix.lower() not in ALLOWED_EXTENSIONS:
        print("Unsupported image type. No photo attached.")
        return None

    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    # Include the ticket ID in the name and avoid overwriting an existing file.
    destination = ATTACHMENTS_DIR / f"{ticket_id}{source.suffix.lower()}"
    counter = 2
    while destination.exists():
        destination = ATTACHMENTS_DIR / f"{ticket_id}_{counter}{source.suffix.lower()}"
        counter += 1

    try:
        shutil.copy2(source, destination)
    except OSError as exc:
        print(f"Could not save the photo: {exc}")
        return None

    relative_path = destination.relative_to(BASE_DIR).as_posix()
    print(f"Photo attached: {relative_path}")
    return relative_path


def open_ticket_photo(ticket):
    """Open the attached image using the computer's default browser/viewer."""
    if not ticket["photo_path"]:
        print("This ticket has no photo attachment.")
        return

    path = Path(ticket["photo_path"])
    if not path.is_absolute():
        path = BASE_DIR / path
    if not path.is_file():
        print("The attachment file could not be found. Check the attachments folder.")
        return

    webbrowser.open(path.resolve().as_uri())
