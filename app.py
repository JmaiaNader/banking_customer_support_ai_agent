import streamlit as st
from banking_agent import BankingSupportSystem

st.set_page_config(page_title="BankAssist AI", page_icon="🏦", layout="wide")

@st.cache_resource
def get_system():
    return BankingSupportSystem()

system = get_system()
st.title("🏦 BankAssist AI")
st.caption("Multi-agent banking customer support demo · Synthetic demo data only")

with st.sidebar:
    st.header("Navigation")
    page = st.radio("Open section", ["Support Assistant", "Ticket Tracker", "History & Logs", "Evaluation Lab", "About"])
    st.divider()
    st.warning("Demo only. Never enter real account numbers, card details, PINs, passwords, or sensitive customer data.")

if page == "Support Assistant":
    st.subheader("How can we help?")
    customer_name = st.text_input("Display name (optional)", placeholder="e.g. Alex")
    message = st.text_area("Your message", placeholder="e.g. My debit card replacement still hasn't arrived.", height=130)
    if st.button("Process message", type="primary"):
        if not message.strip():
            st.error("Please enter a message.")
        else:
            st.session_state["last_result"] = system.handle_message(message.strip(), customer_name.strip() or "Customer")
    result = st.session_state.get("last_result")
    if result:
        st.divider()
        st.subheader("Agent result")
        c1, c2, c3 = st.columns(3)
        c1.metric("Classification", result["classification"])
        c2.metric("Routed agent", result["agent"])
        c3.metric("Ticket", f'#{result["ticket_id"]}' if result.get("ticket_id") else "—")
        st.info(result["response"])
        with st.expander("Execution trace"):
            st.json(result["trace"])

elif page == "Ticket Tracker":
    st.subheader("Support ticket tracker")
    st.write("Create a ticket manually or review requests already saved by the Support Assistant.")

    with st.expander("➕ Create a new support ticket", expanded=True):
        with st.form("create_ticket_form", clear_on_submit=True):
            customer_name = st.text_input("Customer/display name", value="Demo Customer")
            category = st.selectbox("Category", ["General Inquiry", "Debit/Credit Card", "Online Banking", "Transfer/Payment", "Complaint", "Other"])
            summary = st.text_input("Short summary", placeholder="e.g. Debit card replacement has not arrived")
            details = st.text_area("Request details", placeholder="Describe the support request (demo data only).")
            submitted = st.form_submit_button("Create ticket", type="primary")
            if submitted:
                if not summary.strip() or not details.strip():
                    st.error("Please enter both a short summary and request details.")
                else:
                    ticket = system.create_ticket(
                        customer_name=customer_name.strip() or "Demo Customer",
                        summary=f"[{category}] {summary.strip()}",
                        details=details.strip(),
                    )
                    st.success(f'Created ticket #{ticket["ticket_id"]}. It is saved in the local support database.')
                    st.rerun()

    st.divider()
    tickets = system.list_tickets()
    if tickets:
        import pandas as pd
        st.dataframe(pd.DataFrame(tickets), use_container_width=True, hide_index=True)
        ticket_ids = [str(t["ticket_id"]) for t in tickets]
        with st.expander("Update ticket status"):
            selected_id = st.selectbox("Ticket number", ticket_ids)
            current = next(t for t in tickets if str(t["ticket_id"]) == selected_id)
            statuses = ["Unresolved", "Open", "In Progress", "Waiting for Customer", "Resolved", "Closed"]
            current_status = current.get("status", "Open")
            default_index = statuses.index(current_status) if current_status in statuses else 0
            new_status = st.selectbox("New status", statuses, index=default_index)
            if st.button("Save status"):
                system.update_ticket_status(selected_id, new_status)
                st.success(f"Ticket #{selected_id} updated to {new_status}.")
                st.rerun()
    else:
        st.info("No tickets yet. Create one above or submit a support request in Support Assistant.")
    st.caption("All sample records are synthetic. This prototype saves tickets to data/support_tickets.json.")

elif page == "History & Logs":
    st.subheader("Historical messages and agent logs")
    logs = system.list_logs()
    if logs:
        import pandas as pd
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
        selected = st.selectbox("Inspect a log entry", options=list(range(len(logs))),
                                format_func=lambda i: f'{logs[i]["timestamp"]} · {logs[i]["classification"]} · {logs[i]["agent"]}')
        st.json(logs[selected])
    else:
        st.info("No interactions logged yet.")

elif page == "Evaluation Lab":
    st.subheader("Agent evaluation")
    st.write("Run built-in test cases against the classifier and routing logic.")
    if st.button("Run evaluation suite", type="primary"):
        report = system.evaluate()
        st.metric("Routing accuracy", f'{report["routing_accuracy"]:.0%}')
        st.metric("Passed cases", f'{report["passed"]}/{report["total"]}')
        st.dataframe(report["cases"], use_container_width=True, hide_index=True)
        st.caption("This evaluates the demo's rule-based logic, not production banking AI performance.")

else:
    st.subheader("About this prototype")
    st.markdown("""
    **Goal:** demonstrate a multi-agent customer-support workflow for banking.

    **Agents**
    1. **Classifier Agent** — categorizes messages as Positive Feedback, Negative Feedback, or Query.
    2. **Feedback Handler Agent** — thanks customers for positive feedback or creates an unresolved ticket for negative feedback.
    3. **Query Handler Agent** — extracts a six-digit ticket ID and returns its status.

    **Implementation notes**
    - Local JSON files act as a simple support database.
    - Deterministic rules are used; no live bank system or LLM is connected.
    - All seeded examples are synthetic.
    - Do not enter credentials, card numbers, PINs, passwords, or real customer financial information.
    """)
