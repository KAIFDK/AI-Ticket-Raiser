"""
run_tickets.py

What this script does (in plain English):
1. Reads a list of support tickets from tickets.json
2. For each ticket, sends the subject + body to our deployed Toolhouse agent
3. Reads back the agent's JSON classification (category, urgency, etc.)
4. Saves ALL the results together into results.csv and results.json

This is the "glue" script for the Support Ticket Triage Agent challenge.
Toolhouse itself does the hard part (the AI model call, RAG lookup of the
routing policy, etc.) - this script's only job is to feed it tickets one
at a time and collect what comes back.
"""

import requests   # lets us make HTTP calls (the POST request to Toolhouse)
import json       # lets us read/write JSON data
import csv        # lets us write a .csv file
import os         # lets us read settings from environment variables
import time       # lets us pause briefly between requests
from pathlib import Path


# ---------------------------------------------------------------------------
# STEP 0: Configuration
# ---------------------------------------------------------------------------
def load_env_file():
    """Load values from a local .env file if present so the script can use
    environment-based configuration without requiring manual exports."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"").strip("'")
        os.environ.setdefault(key, value)


load_env_file()
# Your deployed agent's URL. After you run `th deploy` (or deploy from the
# Toolhouse UI), Toolhouse gives you a URL that looks like:
#   https://agents.toolhouse.ai/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# Copy that exact URL from your Toolhouse dashboard's "Deploy" tab and paste
# it below, or set it as an environment variable so you don't hardcode it.
AGENT_URL = os.environ.get("TOOLHOUSE_AGENT_URL", "https://agents.toolhouse.ai/b17bee44-f330-4c77-ab30-920fd5806ba3")

# If the user provided a dashboard URL instead of the API endpoint, auto-correct it.
if AGENT_URL.startswith("https://toolhouse.app/"):
    parts = AGENT_URL.strip("/").split("/")
    if len(parts) >= 4:
        AGENT_URL = f"https://agents.toolhouse.ai/{parts[3]}"

# Your Toolhouse API key. Only needed if your agent is set to Private
# (Pro plan). Free-tier agents are public and this can usually stay blank -
# check the exact call format Toolhouse shows you on the Deploy tab; if it
# includes an Authorization header, you'll need this.
TOOLHOUSE_API_KEY = os.environ.get("TOOLHOUSE_API_KEY", "th-fzlOPYXcXypWG3PymVbdGpUg1mrka7lVY7e_WsW8q9g")

# Some Toolhouse deployments expose a public web URL that accepts POST requests
# directly, while others require the authenticated Toolhouse API endpoint.
# We support both by trying the configured URL first and then falling back to
# the documented API pattern when a valid key is available.
TOOLHOUSE_API_BASE = os.environ.get("TOOLHOUSE_API_BASE", "https://api.toolhouse.ai")

INPUT_FILE = "tickets.json"
OUTPUT_CSV = "results.csv"
OUTPUT_JSON = "results.json"


# ---------------------------------------------------------------------------
# STEP 1: Send one ticket to the agent and get back its classification
# ---------------------------------------------------------------------------
def classify_ticket(subject, body):
    """
    Sends one ticket's subject+body to the Toolhouse agent and returns the
    agent's parsed JSON response as a Python dictionary.
    """
    # This is the plain-text message the agent will read - it matches the
    # same "Subject: ... / Body: ..." format we tested in the workbench.
    message_text = f"Subject: {subject}\nBody: {body}"

    headers = {"Content-Type": "application/json"}
    if TOOLHOUSE_API_KEY:
        headers["Authorization"] = f"Bearer {TOOLHOUSE_API_KEY}"

    payloads = [{"message": message_text}]
    if TOOLHOUSE_API_KEY:
        payloads.append({"input": {"message": message_text}})

    last_error = None
    for url in [AGENT_URL, f"{TOOLHOUSE_API_BASE}/chat/web"]:
        for payload in payloads:
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=60,
                )
                if response.status_code >= 400:
                    last_error = RuntimeError(f"{response.status_code} {response.text[:200]}")
                    continue

                raw_text = ""
                for chunk in response.iter_content(decode_unicode=True):
                    if chunk:
                        raw_text += chunk

                cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                return json.loads(cleaned)
            except Exception as exc:
                last_error = exc

    raise RuntimeError(f"Unable to reach Toolhouse agent: {last_error}")


# ---------------------------------------------------------------------------
# STEP 2: Loop over every ticket in tickets.json
# ---------------------------------------------------------------------------
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        tickets = json.load(f)

    results = []

    for ticket in tickets:
        print(f"Processing ticket #{ticket['id']}: {ticket['subject']!r} ...")

        try:
            classification = classify_ticket(ticket["subject"], ticket["body"])
            row = {
                "id": ticket["id"],
                "subject": ticket["subject"],
                "body": ticket["body"],
                "category": classification.get("category"),
                "urgency": classification.get("urgency"),
                "confidence": classification.get("confidence"),
                "routing_team": classification.get("routing_team"),
                "unsure": classification.get("unsure"),
                "reasoning": classification.get("reasoning"),
                "error": "",
            }
        except Exception as e:
            # If a call fails or the response isn't valid JSON, we still
            # record the ticket with the error - so one bad call doesn't
            # kill the whole batch, and the failure itself is visible.
            row = {
                "id": ticket["id"],
                "subject": ticket["subject"],
                "body": ticket["body"],
                "category": "", "urgency": "", "confidence": "",
                "routing_team": "", "unsure": "", "reasoning": "",
                "error": str(e),
            }
            print(f"  -> FAILED: {e}")

        results.append(row)
        time.sleep(1)  # small pause so we don't hammer the API

    # -----------------------------------------------------------------
    # STEP 3: Save everything to results.json and results.csv
    # -----------------------------------------------------------------
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. Processed {len(results)} tickets.")
    print(f"Saved: {OUTPUT_JSON} and {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
