"""
test_agent_output.py

Validates that results.json actually obeys the rules the agent's prompt
promises. Run with: pytest test_agent_output.py -v

These aren't testing the LLM's judgment (that's inherently variable) -
they're testing that the STRUCTURE and HARD RULES of the design are never
broken, no matter what the model decides for a given ticket.
"""

import json
import pytest

VALID_CATEGORIES = {
    "Billing & Payments",
    "Technical / Bug",
    "Account & Access",
    "Feature Request",
    "Complaint / Escalation",
    "General Inquiry",
}

VALID_URGENCY = {"Critical", "High", "Medium", "Low"}


@pytest.fixture
def results():
    with open("results.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_results_file_not_empty(results):
    """We should have processed at least one ticket."""
    assert len(results) > 0


def test_every_ticket_has_a_valid_category(results):
    """Category must be one of the six we defined - never invented."""
    for row in results:
        if row.get("error"):
            continue  # skip rows that failed the API call itself
        assert row["category"] in VALID_CATEGORIES, (
            f"Ticket {row['id']} has an invalid category: {row['category']!r}"
        )


def test_every_ticket_has_a_valid_urgency(results):
    """Urgency must be one of Critical/High/Medium/Low."""
    for row in results:
        if row.get("error"):
            continue
        assert row["urgency"] in VALID_URGENCY, (
            f"Ticket {row['id']} has an invalid urgency: {row['urgency']!r}"
        )


def test_confidence_is_between_0_and_1(results):
    """Confidence score must be a valid probability."""
    for row in results:
        if row.get("error"):
            continue
        confidence = float(row["confidence"])
        assert 0.0 <= confidence <= 1.0, (
            f"Ticket {row['id']} has an out-of-range confidence: {confidence}"
        )


def test_unsure_tickets_always_route_to_human_review(results):
    """
    This is THE core business rule of the agent: if unsure is true,
    routing_team MUST be exactly 'Human Review' - no exceptions.
    This is the exact bug we found and fixed during manual testing;
    this test proves it stays fixed.
    """
    for row in results:
        if row.get("error"):
            continue
        if row["unsure"] in (True, "true", "True"):
            assert row["routing_team"] == "Human Review", (
                f"Ticket {row['id']} is marked unsure=True but was routed "
                f"to {row['routing_team']!r} instead of 'Human Review'"
            )


def test_low_confidence_tickets_are_flagged_unsure(results):
    """
    Any ticket scored below the 0.6 threshold should have been flagged
    unsure, per the design's confidence policy.
    """
    for row in results:
        if row.get("error"):
            continue
        confidence = float(row["confidence"])
        if confidence < 0.6:
            assert row["unsure"] in (True, "true", "True"), (
                f"Ticket {row['id']} has confidence {confidence} (<0.6) "
                f"but unsure was not set to True"
            )
