from ticket import Ticket


class Admin:

    def __init__(self, username, password):
        self.username = username
        self.password = password

    # ==========================
    # LOGIN
    # ==========================

    def login(self, username, password):

        if username == self.username and password == self.password:
            return True

        return False

    # ==========================
    # VIEW RECEIVED TICKETS
    # ==========================

    def view_tickets(self, tickets):

        print("\n====== RECEIVED TICKETS ======")

        if len(tickets) == 0:
            print("No tickets received.")
            return

        for ticket in tickets:

            print("\n------------------------------")
            print(f"Ticket ID: {ticket.ticket_id}")
            print(f"Title: {ticket.title}")
            print(f"Description: {ticket.description}")
            print(f"Username: {ticket.username}")
            print(f"Status: {ticket.status}")

            if ticket.assigned_to:
                print(f"Assigned To: {ticket.assigned_to}")
            else:
                print("Assigned To: Not assigned")

            print(f"Created At: {ticket.created_at}")

    # ==========================
    # CONFIRM TICKET
    # ==========================

    def confirm_ticket(self, ticket):

        print("\n====== TICKET CONFIRMATION ======")
        print(f"Ticket ID: {ticket.ticket_id}")
        print(f"Submitted by: {ticket.username}")
        print("Ticket received successfully!")

    # ==========================
    # SEARCH TICKET
    # ==========================

    def search_ticket(self, tickets, ticket_id):

        for ticket in tickets:

            if ticket.ticket_id == ticket_id:
                return ticket

        return None

    # ==========================
    # ASSIGN TICKET
    # ==========================

    def assign_ticket(self, ticket, assigned_to):

        ticket.assigned_to = assigned_to

        print("\nTicket assigned successfully!")
        print(f"Ticket ID: {ticket.ticket_id}")
        print(f"Assigned To: {ticket.assigned_to}")

    # ==========================
    # UPDATE STATUS
    # ==========================

    def update_ticket_status(self, ticket, new_status):

        ticket.update_status(new_status)

        print("\nTicket status updated successfully!")
        print(f"Ticket ID: {ticket.ticket_id}")
        print(f"New Status: {ticket.status}")


# ==========================================
# ADMIN MENU
# ==========================================

def admin_menu(admin, tickets):

    while True:

        print("\n================================")
        print("        ADMIN DASHBOARD")
        print("================================")
        print("1. View Received Tickets")
        print("2. Confirm Ticket")
        print("3. Search Ticket")
        print("4. Assign Ticket")
        print("5. Update Ticket Status")
        print("6. Logout")
        print("================================")

        choice = input("Enter choice: ")

        # VIEW
        if choice == "1":

            admin.view_tickets(tickets)

        # CONFIRM
        elif choice == "2":

            ticket_id = input("Enter Ticket ID: ")

            ticket = admin.search_ticket(tickets, ticket_id)

            if ticket:
                admin.confirm_ticket(ticket)
            else:
                print("\nTicket not found.")

        # SEARCH
        elif choice == "3":

            ticket_id = input("Enter Ticket ID: ")

            ticket = admin.search_ticket(tickets, ticket_id)

            if ticket:

                print("\n====== TICKET FOUND ======")
                print(f"Ticket ID: {ticket.ticket_id}")
                print(f"Title: {ticket.title}")
                print(f"Description: {ticket.description}")
                print(f"Username: {ticket.username}")
                print(f"Status: {ticket.status}")

                if ticket.assigned_to:
                    print(f"Assigned To: {ticket.assigned_to}")
                else:
                    print("Assigned To: Not assigned")

                print(f"Created At: {ticket.created_at}")

            else:
                print("\nTicket not found.")

        # ASSIGN
        elif choice == "4":

            ticket_id = input("Enter Ticket ID: ")

            ticket = admin.search_ticket(tickets, ticket_id)

            if ticket:

                print("\n====== ASSIGN TICKET ======")
                print("1. IT Staff 01")
                print("2. IT Staff 02")
                print("3. Network Support")
                print("4. Hardware Support")

                staff_choice = input("Choose personnel: ")

                if staff_choice == "1":
                    assigned_to = "IT Staff 01"

                elif staff_choice == "2":
                    assigned_to = "IT Staff 02"

                elif staff_choice == "3":
                    assigned_to = "Network Support"

                elif staff_choice == "4":
                    assigned_to = "Hardware Support"

                else:
                    print("\nInvalid choice.")
                    continue

                admin.assign_ticket(ticket, assigned_to)

            else:
                print("\nTicket not found.")

        # UPDATE STATUS
        elif choice == "5":

            ticket_id = input("Enter Ticket ID: ")

            ticket = admin.search_ticket(tickets, ticket_id)

            if ticket:

                print("\n====== UPDATE TICKET STATUS ======")
                print("1. Open")
                print("2. Pending")
                print("3. In Progress")
                print("4. Resolved")
                print("5. Cancelled")

                status_choice = input("Choose status: ")

                if status_choice == "1":
                    status = "Open"

                elif status_choice == "2":
                    status = "Pending"

                elif status_choice == "3":
                    status = "In Progress"

                elif status_choice == "4":
                    status = "Resolved"

                elif status_choice == "5":
                    status = "Cancelled"

                else:
                    print("\nInvalid choice.")
                    continue

                admin.update_ticket_status(ticket, status)

            else:
                print("\nTicket not found.")

        # LOGOUT
        elif choice == "6":

            print("\nLogging out...")
            break

        else:

            print("\nInvalid choice. Please try again.")