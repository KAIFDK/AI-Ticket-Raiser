import json
import csv
import sys
from pathlib import Path
from run_tickets import classify_ticket

TICKETS_FILE = Path("tickets.json")
OUTPUT_JSON = Path("results.json")
OUTPUT_CSV = Path("results.csv")

def load_json_file(file_path):
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_json_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def save_csv_file(file_path, data):
    if not data:
        return
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)

def main():
    print("=" * 60)
    print("         SINGLE TICKET EXECUTION INTERFACE")
    print("=" * 60)

    # 1. Load tickets
    tickets = load_json_file(TICKETS_FILE)
    if not tickets:
        print("No tickets found in tickets.json! Please add tickets first.")
        return

    # 2. Display available tickets
    print("Available Tickets:")
    for ticket in tickets:
        print(f"  [{ticket.get('id')}] - {ticket.get('subject')}")
    print("-" * 60)

    # 3. Prompt user for ID
    try:
        selection = input("Enter the ID of the ticket to execute: ").strip()
        if not selection:
            print("No ID entered. Exiting.")
            return
        
        ticket_id = int(selection)
    except ValueError:
        print("Invalid numeric ID. Exiting.")
        return
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")
        return

    # 4. Find the selected ticket
    selected_ticket = next((t for t in tickets if t.get("id") == ticket_id), None)
    if not selected_ticket:
        print(f"Error: Ticket with ID {ticket_id} not found.")
        return

    print("-" * 60)
    print(f"Executing Classification for Ticket #{ticket_id}...")
    print(f"Subject: {selected_ticket['subject']}")
    print(f"Body: {selected_ticket['body']}")
    print("-" * 60)

    # 5. Classify the ticket
    try:
        classification = classify_ticket(selected_ticket["subject"], selected_ticket["body"])
        
        # Format the result row
        row = {
            "id": selected_ticket["id"],
            "subject": selected_ticket["subject"],
            "body": selected_ticket["body"],
            "category": classification.get("category"),
            "urgency": classification.get("urgency"),
            "confidence": classification.get("confidence"),
            "routing_team": classification.get("routing_team"),
            "unsure": classification.get("unsure"),
            "reasoning": classification.get("reasoning"),
            "error": "",
        }
        
        # Display the result beautifully
        print("\nCLASSIFICATION RESULTS:")
        print(f"  Category:     {row['category']}")
        print(f"  Urgency:      {row['urgency']}")
        print(f"  Confidence:   {row['confidence']}")
        print(f"  Routing Team: {row['routing_team']}")
        print(f"  Unsure:       {row['unsure']}")
        print(f"  Reasoning:    {row['reasoning']}")
        print("=" * 60)
        
    except Exception as e:
        row = {
            "id": selected_ticket["id"],
            "subject": selected_ticket["subject"],
            "body": selected_ticket["body"],
            "category": "", "urgency": "", "confidence": "",
            "routing_team": "", "unsure": "", "reasoning": "",
            "error": str(e),
        }
        print(f"\nExecution FAILED: {e}")
        print("=" * 60)

    # 6. Update results in JSON and CSV outputs
    results = load_json_file(OUTPUT_JSON)
    
    # Check if a result for this ID already exists and update/replace it
    existing_index = next((i for i, r in enumerate(results) if r.get("id") == ticket_id), None)
    if existing_index is not None:
        results[existing_index] = row
    else:
        results.append(row)

    # Ensure results are sorted by ID
    results.sort(key=lambda r: r.get("id", 0))

    # Save files
    try:
        save_json_file(OUTPUT_JSON, results)
        save_csv_file(OUTPUT_CSV, results)
        print("Saved updated classification to results.json and results.csv")
    except Exception as e:
        print(f"Error saving results: {e}")

if __name__ == "__main__":
    main()
