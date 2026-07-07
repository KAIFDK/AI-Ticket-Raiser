import json
from pathlib import Path

TICKETS_FILE = Path("tickets.json")

def main():
    print("=" * 50)
    print("         SUPPORT TICKET CREATOR INTERFACE")
    print("=" * 50)

    # 1. Load existing tickets
    if TICKETS_FILE.exists():
        try:
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                tickets = json.load(f)
        except Exception as e:
            print(f"Error reading existing tickets: {e}")
            tickets = []
    else:
        tickets = []

    # 2. Determine the next Ticket ID
    if tickets:
        # Get the maximum ID currently present and increment by 1
        next_id = max(ticket.get("id", 0) for ticket in tickets) + 1
    else:
        next_id = 1

    print(f"Creating Ticket #{next_id}")
    print("-" * 50)

    # 3. Prompt user for input
    try:
        subject = input("Enter Subject: ").strip()
        while not subject:
            print("Subject cannot be empty.")
            subject = input("Enter Subject: ").strip()

        body = input("Enter Body: ").strip()
        while not body:
            print("Body cannot be empty.")
            body = input("Enter Body: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")
        return

    # 4. Create the new ticket object
    new_ticket = {
        "id": next_id,
        "subject": subject,
        "body": body
    }

    # 5. Append and save
    tickets.append(new_ticket)
    try:
        with open(TICKETS_FILE, "w", encoding="utf-8") as f:
            json.dump(tickets, f, indent=2)
        print("-" * 50)
        print(f"Success! Ticket #{next_id} successfully added to tickets.json.")
        print(f"Subject: {subject}")
        print("=" * 50)
    except Exception as e:
        print(f"Error writing to tickets.json: {e}")

if __name__ == "__main__":
    main()
