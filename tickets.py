import random
from datetime import datetime


class Ticket:
    def __init__(
        self,
        ticket_id,
        title,
        description,
        status='Open',
        created_at=None,
        username=None,
        assigned_to=None
    ):
        self.ticket_id = ticket_id
        self.title = title
        self.description = description
        self.status = status
        self.created_at = created_at if created_at else datetime.now()
        self.username = username
        self.assigned_to = assigned_to

    def update_status(self, new_status):
        self.status = new_status

    def __str__(self):
        return (
            f"Ticket ID: {self.ticket_id}, "
            f"Title: {self.title}, "
            f"Status: {self.status}, "
            f"Created At: {self.created_at}"
        )


# Store existing ticket IDs
existing_ticket_ids = set()


def generate_ticket_id():

    while True:
        number = random.randint(10000, 99999)
        ticket_id = f"TCK-{number}"

        # Make sure the ID not already used
        if ticket_id not in existing_ticket_ids:
            existing_ticket_ids.add(ticket_id)
            return ticket_id


def create_ticket():

    print("\n====== Create a New Ticket ======")

    title = input("Enter the title of the ticket: ")
    description = input("Describe the issue: ")
    username = input("Enter your username: ")

    # Generate a unique ticket ID
    ticket_id = generate_ticket_id()

    # Create Ticket object
    new_ticket = Ticket(
        ticket_id,
        title,
        description,
        username=username
    )

    print("\nTicket created successfully!")
    print(f"Ticket ID: {new_ticket.ticket_id}")

    return new_ticket


def print_ticket(ticket):

    print("\n====== Ticket Details ======")
    print(f"Ticket ID: {ticket.ticket_id}")
    print(f"Title: {ticket.title}")
    print(f"Description: {ticket.description}")
    print(f"Status: {ticket.status}")
    print(f"Created At: {ticket.created_at}")
    print(f"Username: {ticket.username}")
