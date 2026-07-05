from datetime import date

import streamlit as st
from agent import run_agent
from artifacts import render_artifact
from booking_dialogs import booking_success_dialog, cancellation_success_dialog, confirm_booking_dialog, confirm_cancellation_dialog
from ui_components import add_artifact_ids


def render_agent_view(user: dict) -> None:
    st.subheader("Buchungsagent")

    if "pending_booking_request" in st.session_state:
        confirm_booking_dialog(user)

    if "pending_cancellation_booking" in st.session_state:
        confirm_cancellation_dialog(user)

    if "last_created_booking" in st.session_state:
        booking_success_dialog()

    if "last_cancelled_booking" in st.session_state:
        cancellation_success_dialog()

    if "agent_messages" not in st.session_state:
        st.session_state["agent_messages"] = []

    for message in st.session_state["agent_messages"]:
        message["artifacts"] = add_artifact_ids(message.get("artifacts", []))

    for message in st.session_state["agent_messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

            for artifact in message.get("artifacts", []):
                if artifact.get("type") == "booking_confirmation_required":
                    continue

                render_artifact(artifact)

    prompt = st.chat_input("Was möchtest du tun?")

    if prompt:
        st.session_state["agent_messages"].append(
            {
                "role": "user",
                "content": prompt,
                "artifacts": [],
            }
        )

        with st.spinner("Agent denkt nach..."):
            result = run_agent(
                user_message=prompt,
                messages=st.session_state["agent_messages"],
                current_user=user,
            )

        assistant_artifacts = add_artifact_ids(result.get("artifacts", []))

        handle_agent_artifacts(assistant_artifacts)

        st.session_state["agent_messages"].append(
            {
                "role": "assistant",
                "content": result["content"],
                "artifacts": assistant_artifacts,
            }
        )

        st.rerun()

def handle_agent_artifacts(artifacts: list[dict]) -> None:
    for artifact in artifacts:
        if artifact.get("type") != "booking_confirmation_required":
            continue

        data = artifact["data"]

        st.session_state["pending_booking_request"] = {
            "guest_name": data["guest_name"],
            "guest_email": data["guest_email"],
            "start_date": date.fromisoformat(data["start_date"]),
            "end_date": date.fromisoformat(data["end_date"]),
            "guests": int(data["guests"]),
            "notes": data.get("notes", ""),
            "created_by": data.get("created_by", ""),
        }

        # st.session_state["active_view"] = "create_booking"

        st.rerun()