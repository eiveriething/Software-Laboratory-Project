from database import add_notification, get_notifications, mark_notification_read


def notify_user(username, ticket_id, event_message):
    """Save an in-app notification for the requester."""
    message = f"Ticket {ticket_id}: {event_message}"
    add_notification(username, message, ticket_id)


def show_notifications(username):
    notifications = get_notifications(username)
    print("\n====== YOUR NOTIFICATIONS ======")
    if not notifications:
        print("You have no notifications.")
        return

    for item in notifications:
        status = "Read" if item["is_read"] else "Unread"
        print(f'[{item["notification_id"]}] [{status}] {item["created_at"]}')
        print(f'    {item["message"]}')

    choice = input("\nEnter notification ID to mark as read (or press Enter to return): ").strip()
    if choice.isdigit():
        mark_notification_read(int(choice), username)
        print("Notification marked as read.")
