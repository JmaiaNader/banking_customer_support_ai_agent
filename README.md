# BankAssist AI — Banking Customer Support Multi-Agent Demo

A Streamlit application based on the supplied capstone problem statement.

## Features
- Classifier Agent: routes messages to Positive Feedback, Negative Feedback, or Query.
- Feedback Handler Agent: acknowledges positive feedback or creates a unique six-digit unresolved support ticket for negative feedback.
- Query Handler Agent: extracts a six-digit ticket ID and looks up its status; a new support request without a ticket ID is saved as a new ticket.
- Ticket Tracker: create tickets manually, view saved support tickets, and update ticket statuses.
- History & Logs: review interactions, routing, and execution traces.
- Evaluation Lab: run built-in classification/routing tests.

## Run in VS Code (Windows)
1. Extract the ZIP and open the `banking_customer_support_ai_agent` folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat`.
4. Install packages:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Run:
   ```bash
   streamlit run app.py
   ```

## Project structure
```text
banking_customer_support_ai_agent/
├── app.py
├── banking_agent.py
├── requirements.txt
├── README.md
├── .gitignore
└── data/
    ├── support_tickets.json
    └── agent_logs.json
```

## Scope and safety
This is an educational prototype using deterministic rules and local JSON files. It does not connect to a bank, payment network, account system, or live support platform, and no hosted LLM is connected. All seeded records are synthetic. Never enter account numbers, card details, PINs, passwords, one-time codes, or real customer financial information. Real deployment requires authentication, authorization, secure storage, audit controls, privacy review, and bank-approved APIs. Local JSON files may not persist across hosted redeployments.
