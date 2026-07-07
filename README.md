# Support Ticket Triage Agent Classifier

This project is the batch processing glue code for the Support Ticket Triage Agent challenge. It reads a list of customer support tickets, submits them to a deployed AI agent in Toolhouse for classification (category, urgency, confidence, routing, and reasoning), and saves the aggregated outcomes into structured formats (`results.json` and `results.csv`).

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Setup & Installation](#setup--installation)
3. [Configuration](#configuration)
4. [Running the Classifier](#running-the-classifier)
5. [Sample Inputs and Outputs](#sample-inputs-and-outputs)
6. [Design Tradeoffs & Robustness Decisions](#design-tradeoffs--robustness-decisions)

---

## Prerequisites
- **Python 3.8+**
- A **Toolhouse** account with a deployed Agent.

---

## Setup & Installation

1. **Create and Activate a Virtual Environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

The project is pre-configured with working default credentials directly in the script, allowing you to run it immediately out-of-the-box. 

If you wish to use your own Toolhouse agent instead, you can create a `.env` file in the root directory (or update the existing one) with your credentials:

```env
TOOLHOUSE_AGENT_URL=https://agents.toolhouse.ai/YOUR_AGENT_ID
TOOLHOUSE_API_KEY=your-toolhouse-api-key
```

### URL Safeguard
If you paste the dashboard URL (e.g., `https://toolhouse.app/<workspace_id>/<agent_id>`) into `TOOLHOUSE_AGENT_URL` by mistake, the script is equipped with an auto-correction parser that automatically extracts the agent ID and translates it to the correct endpoint (`https://agents.toolhouse.ai/<agent_id>`).

---

## Running the Classifier

Run the main execution script:
```bash
python run_tickets.py
```

Upon completion, it will output logs for each ticket processed and save the results into:
- `results.json` (Structured JSON representation)
- `results.csv` (Tabular format, ready for spreadsheet import)

---

## Sample Inputs and Outputs

### Sample Input (`tickets.json`)
```json
[
  {
    "id": 1,
    "subject": "Everything is down",
    "body": "None of our users can log in since 9am. This is affecting our entire company account. Please help immediately."
  },
  {
    "id": 4,
    "subject": "How do I change my invoice email?",
    "body": "Just wondering where in settings I can update the email address invoices get sent to."
  }
]
```

### Sample Output (`results.json`)
```json
[
  {
    "id": 1,
    "subject": "Everything is down",
    "body": "None of our users can log in since 9am. This is affecting our entire company account. Please help immediately.",
    "category": "Technical / Bug",
    "urgency": "Critical",
    "confidence": 0.98,
    "routing_team": "Engineering",
    "unsure": false,
    "reasoning": "The phrases \"None of our users can log in since 9am\" and \"affecting our entire company account\" indicate a system-wide login outage, which fits Technical / Bug and meets the Critical urgency definition.",
    "error": ""
  },
  {
    "id": 4,
    "subject": "How do I change my invoice email?",
    "body": "Just wondering where in settings I can update the email address invoices get sent to.",
    "category": "Billing & Payments",
    "urgency": "Low",
    "confidence": 0.98,
    "routing_team": "Billing Team",
    "unsure": false,
    "reasoning": "The phrases \"invoice email\" and \"update the email address invoices get sent to\" indicate a billing-related how-to question, which fits Billing & Payments with low urgency.",
    "error": ""
  }
]
```

---

## Design Tradeoffs & Robustness Decisions

- **Error Isolation**:
  * *Tradeoff*: Catching exceptions per ticket rather than raising them immediately.
  * *Decision*: Individual HTTP or parser failures will not halt the entire batch. If a ticket request fails (e.g. due to payload parsing issues, or single network timeouts), the error message is recorded under the `"error"` attribute in the final files, and the loop proceeds to process subsequent tickets.
- **Payload & Endpoint Compatibility fallback**:
  * *Tradeoff*: Toolhouse deployments accept slightly different payload schemas depending on whether they run on the public web endpoints or private API proxies.
  * *Decision*: The classification runner sequentially attempts multiple endpoints and request configurations (e.g., wrapping requests under `"message"` vs `"input: {message}"`), allowing the same python agent client to be highly compatible across free-tier public deployments, local web proxies, or enterprise API accounts.
- **API Courtesy & Rate Limiting**:
  * *Tradeoff*: Iterating through a large corpus of tickets could trigger rate limiting from the LLM or Toolhouse API endpoints.
  * *Decision*: An artificial 1-second delay (`time.sleep(1)`) is introduced after each classification. While this makes the batch process slightly slower, it provides a safe buffer against rate limits and server overload.
