"""Streamlit interface for the competitor analysis agent."""

import os
from uuid import uuid4

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from src.graph import build_graph, new_state


st.set_page_config(page_title="Competitor Analysis Agent")
st.title("Competitor Analysis Agent")
st.write("Research competitors, review sourced findings, and save an approved briefing.")

load_dotenv()
required_variables = ("TAVILY_API_KEY", "NEBIUS_API_KEY", "NEBIUS_MODEL")
missing_variables = [
    variable for variable in required_variables if not os.getenv(variable, "").strip()
]
if missing_variables:
    st.error(f"Missing required environment variables: {', '.join(missing_variables)}")
    st.stop()


# Initialize graph resources and run state once per Streamlit session.
if "graph" not in st.session_state:
    st.session_state.graph = build_graph(MemorySaver())
    st.session_state.thread_id = str(uuid4())
    st.session_state.stage = "input"
    st.session_state.interrupt_payload = None
    st.session_state.final_state = {}


# Store an interrupted or completed graph result in the session state.
def handle_graph_result(result: dict) -> None:
    """Set the next UI stage from a graph invocation result."""
    interrupts = result.get("__interrupt__")
    if interrupts:
        payload = interrupts[0].value
        st.session_state.interrupt_payload = payload
        st.session_state.stage = payload["type"]
    else:
        st.session_state.final_state = result
        st.session_state.interrupt_payload = None
        st.session_state.stage = "done"


# Invoke or resume the graph without exposing exception details.
def call_graph(graph_input: dict | Command) -> bool:
    """Run the graph and return whether the invocation completed safely."""
    try:
        result = st.session_state.graph.invoke(
            graph_input,
            {"configurable": {"thread_id": st.session_state.thread_id}},
        )
        handle_graph_result(result)
        return True
    except Exception as error:
        st.error(f"Graph call failed: {type(error).__name__}")
        return False


# Reset only the current run while keeping the compiled graph for this session.
def start_new_analysis() -> None:
    """Clear run data and assign a fresh checkpoint thread ID."""
    st.session_state.thread_id = str(uuid4())
    st.session_state.stage = "input"
    st.session_state.interrupt_payload = None
    st.session_state.final_state = {}


if st.session_state.stage == "input":
    company = st.text_input("Company name")
    if st.button("Start analysis"):
        if not company.strip():
            st.error("Enter a company name to start the analysis.")
        else:
            with st.spinner("Finding competitors..."):
                completed = call_graph(new_state(company.strip()))
            if completed:
                st.rerun()

elif st.session_state.stage == "approve_competitors":
    payload = st.session_state.interrupt_payload
    st.subheader("Approve competitors")
    st.write("Review, edit, add, or remove competitors before research begins.")
    rows = payload["competitors"]
    edited_competitors = st.data_editor(
        pd.DataFrame(rows, columns=["name", "website", "reason"]),
        column_config={
            "name": "Name",
            "website": "Website",
            "reason": "Reason",
        },
        num_rows="dynamic",
        key="competitor_editor",
    )
    approve_column, reject_column = st.columns(2)
    if approve_column.button("Approve and continue"):
        edited_rows = edited_competitors.fillna("").to_dict(orient="records")
        with st.spinner("Researching, extracting and reviewing... this takes a few minutes"):
            completed = call_graph(Command(resume={"approved": True, "competitors": edited_rows}))
        if completed:
            st.rerun()
    if reject_column.button("Reject"):
        with st.spinner("Finishing analysis..."):
            completed = call_graph(Command(resume={"approved": False}))
        if completed:
            st.rerun()

elif st.session_state.stage == "approve_briefing":
    payload = st.session_state.interrupt_payload
    st.subheader("Approve briefing")
    with st.expander("Review flags", expanded=False):
        if payload["review_flags"]:
            for flag in payload["review_flags"]:
                st.write(f"- {flag}")
        else:
            st.write("None")
    with st.expander("Run issues", expanded=False):
        if payload["errors"]:
            for error in payload["errors"]:
                st.write(f"- {error}")
        else:
            st.write("None")

    edited_briefing = st.text_area(
        "Briefing Markdown",
        value=payload["briefing"],
        height=420,
        key="briefing_editor",
    )
    st.subheader("Preview")
    st.markdown(edited_briefing)
    approve_column, reject_column = st.columns(2)
    if approve_column.button("Approve and save"):
        with st.spinner("Saving briefing..."):
            completed = call_graph(Command(resume={"approved": True, "briefing": edited_briefing}))
        if completed:
            st.rerun()
    if reject_column.button("Reject, do not save"):
        with st.spinner("Finishing analysis..."):
            completed = call_graph(Command(resume={"approved": False}))
        if completed:
            st.rerun()

elif st.session_state.stage == "done":
    result = st.session_state.final_state
    saved_path = result.get("saved_path", "")
    errors = result.get("errors", [])
    briefing = result.get("briefing", "")
    if saved_path:
        st.success(f"Briefing saved to: {saved_path}")
    else:
        st.info("Nothing was saved.")
        for error in errors:
            st.write(f"- {error}")

    if briefing:
        st.subheader("Final briefing")
        st.markdown(briefing)
    st.download_button(
        "Download briefing Markdown",
        data=briefing,
        file_name="competitor_briefing.md",
        mime="text/markdown",
    )
    if st.button("Start a new analysis"):
        start_new_analysis()
        st.rerun()
