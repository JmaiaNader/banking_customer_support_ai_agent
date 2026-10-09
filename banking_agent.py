"""Educational multi-agent banking support workflow using synthetic data."""
import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
TICKETS_FILE = DATA_DIR / "support_tickets.json"
LOGS_FILE = DATA_DIR / "agent_logs.json"

SEED_TICKETS = [
    {"ticket_id": "650932", "customer_name": "Demo Customer", "summary": "Net banking login issue", "status": "Resolved", "created_at": "2026-09-20T10:00:00+00:00"},
    {"ticket_id": "721406", "customer_name": "Demo Customer", "summary": "Debit card replacement delay", "status": "In Progress", "created_at": "2026-10-01T12:30:00+00:00"},
]

def read_json(path, fallback):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        write_json(path, fallback)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return fallback

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

class ClassifierAgent:
    POSITIVE = ("thank", "thanks", "great service", "appreciate", "excellent", "resolved", "happy")
    NEGATIVE = ("still hasn't", "still has not", "not arrived", "delay", "delayed", "unhappy", "poor", "complaint", "frustrated", "inconvenience", "not working", "can't", "cannot", "failed", "issue", "problem", "missing")

    def classify(self, message):
        text = message.lower()
        if re.search(r"\b(ticket|case)\s*#?\s*\d{6}\b", text) and any(w in text for w in ("status", "check", "track", "update", "where", "resolved", "progress")):
            return "Query"
        if any(word in text for word in self.NEGATIVE):
            return "Negative Feedback"
        if any(word in text for word in self.POSITIVE):
            return "Positive Feedback"
        return "Query"

class FeedbackHandlerAgent:
    def handle(self, message, customer_name):
        tickets = read_json(TICKETS_FILE, SEED_TICKETS)
        lower = message.lower()
        if not any(word in lower for word in ClassifierAgent.NEGATIVE):
            return {"classification": "Positive Feedback", "agent": "Feedback Handler Agent", "ticket_id": None,
                    "response": f"Thank you for your feedback, {customer_name}! We're delighted to assist you.",
                    "trace": ["Classifier Agent → Positive Feedback", "Feedback Handler Agent → personalized acknowledgement"]}
        used = {str(t["ticket_id"]) for t in tickets}
        while True:
            ticket_id = f"{secrets.randbelow(1_000_000):06d}"
            if ticket_id != "000000" and ticket_id not in used:
                break
        ticket = {"ticket_id": ticket_id, "customer_name": customer_name, "summary": message[:160],
                  "status": "Unresolved", "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        tickets.append(ticket)
        write_json(TICKETS_FILE, tickets)
        return {"classification": "Negative Feedback", "agent": "Feedback Handler Agent", "ticket_id": ticket_id,
                "response": f"We apologize for the inconvenience. A new ticket #{ticket_id} has been created, and our support team will follow up.",
                "trace": ["Classifier Agent → Negative Feedback", "Feedback Handler Agent → generated unique ticket ID", "Support database → inserted unresolved ticket"]}

class QueryHandlerAgent:
    def handle(self, message):
        match = re.search(r"\b(?:ticket|case)\s*#?\s*(\d{6})\b", message, re.IGNORECASE)
        if not match:
            # A new support request (not a ticket-status lookup) should be persisted as a ticket.
            system = BankingSupportSystem()
            ticket = system.create_ticket(
                customer_name="Customer",
                summary=message[:160],
                details=message,
                status="Open",
            )
            return {"classification": "Query", "agent": "Query Handler Agent", "ticket_id": ticket["ticket_id"],
                    "response": f'Your support request has been saved as ticket #{ticket["ticket_id"]}. Current status: {ticket["status"]}.',
                    "trace": ["Classifier Agent → Query / support request", "Query Handler Agent → no existing ticket ID supplied",
                              f'Support database → created ticket #{ticket["ticket_id"]} with status {ticket["status"]}']}
        ticket_id = match.group(1)
        tickets = read_json(TICKETS_FILE, SEED_TICKETS)
        ticket = next((t for t in tickets if str(t["ticket_id"]) == ticket_id), None)
        if ticket:
            response = f'Your ticket #{ticket_id} is currently marked as: {ticket["status"]}.'
            trace = ["Classifier Agent → Query", f"Query Handler Agent → extracted ticket ID {ticket_id}", "Support database → ticket found"]
        else:
            response = f"I couldn't find ticket #{ticket_id} in this demo database. Please verify the number or contact your bank through its official channel."
            trace = ["Classifier Agent → Query", f"Query Handler Agent → extracted ticket ID {ticket_id}", "Support database → ticket not found"]
        return {"classification": "Query", "agent": "Query Handler Agent", "ticket_id": ticket_id, "response": response, "trace": trace}

class BankingSupportSystem:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        read_json(TICKETS_FILE, SEED_TICKETS)
        read_json(LOGS_FILE, [])
        self.classifier = ClassifierAgent()
        self.feedback_agent = FeedbackHandlerAgent()
        self.query_agent = QueryHandlerAgent()

    def create_ticket(self, customer_name="Demo Customer", summary="", details="", status="Open"):
        tickets = read_json(TICKETS_FILE, SEED_TICKETS)
        used = {str(t.get("ticket_id", "")) for t in tickets}
        while True:
            ticket_id = f"{secrets.randbelow(1_000_000):06d}"
            if ticket_id != "000000" and ticket_id not in used:
                break
        ticket = {
            "ticket_id": ticket_id,
            "customer_name": customer_name or "Demo Customer",
            "summary": summary or (details[:160] if details else "Support request"),
            "details": details or summary,
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        tickets.append(ticket)
        write_json(TICKETS_FILE, tickets)
        return ticket

    def update_ticket_status(self, ticket_id, status):
        tickets = read_json(TICKETS_FILE, SEED_TICKETS)
        for ticket in tickets:
            if str(ticket.get("ticket_id")) == str(ticket_id):
                ticket["status"] = status
                ticket["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                write_json(TICKETS_FILE, tickets)
                return ticket
        return None

    def handle_message(self, message, customer_name="Customer"):
        classification = self.classifier.classify(message)
        if classification in ("Positive Feedback", "Negative Feedback"):
            result = self.feedback_agent.handle(message, customer_name)
        else:
            result = self.query_agent.handle(message)
        log = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "message": message,
               "classification": result["classification"], "agent": result["agent"],
               "ticket_id": result.get("ticket_id"), "response": result["response"], "trace": result["trace"]}
        logs = read_json(LOGS_FILE, [])
        logs.append(log)
        write_json(LOGS_FILE, logs[-1000:])
        return result

    def list_tickets(self):
        return read_json(TICKETS_FILE, SEED_TICKETS)

    def list_logs(self):
        return list(reversed(read_json(LOGS_FILE, [])))

    def evaluate(self):
        tests = [
            ("Thanks for resolving my net banking issue.", "Positive Feedback"),
            ("My debit card replacement still hasn't arrived.", "Negative Feedback"),
            ("I am frustrated that my transfer issue is not working.", "Negative Feedback"),
            ("Could you check the status of ticket 650932?", "Query"),
            ("Track ticket #721406 status please.", "Query"),
            ("Can you check ticket 111222?", "Query"),
        ]
        cases = []
        for message, expected in tests:
            actual = self.classifier.classify(message)
            cases.append({"message": message, "expected": expected, "actual": actual, "passed": actual == expected})
        passed = sum(1 for row in cases if row["passed"])
        return {"passed": passed, "total": len(cases), "routing_accuracy": passed / len(cases), "cases": cases}
