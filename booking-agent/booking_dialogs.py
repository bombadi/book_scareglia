from datetime import date, datetime, timedelta

import streamlit as st

from bookings import cancel_booking, create_booking, update_booking
from mailer import (
    send_booking_cancellation_email,
    send_booking_confirmation_email,
    send_booking_update_email,
)


def parse_booking_date(value: str) -> date:
    return datetime.strptime(value, "%d.%m.%Y").date()


def set_booking_email_status(
    success_key: str,
    message_key: str,
    email_result: dict | None,
    success_message: str,
    failure_message: str,
) -> None:
    if email_result and email_result.get("success"):
        st.session_state[success_key] = True
        st.session_state[message_key] = success_message
    else:
        st.session_state[success_key] = False
        st.session_state[message_key] = failure_message

@st.dialog("Buchung bestätigen")
def confirm_booking_dialog(user: dict) -> None:
    booking_request = st.session_state.get("pending_booking_request")

    if not booking_request:
        st.warning("Es liegen keine Buchungsdaten zur Bestätigung vor.")
        return

    st.write("Bitte prüfe die Buchungsdaten, bevor du die Buchung verbindlich erstellst.")

    st.markdown("### Buchungsdetails")
    st.write(f"**Name:** {booking_request['guest_name']}")
    st.write(f"**E-Mail:** {booking_request['guest_email']}")
    st.write(f"**Anreise:** {booking_request['start_date'].strftime('%d.%m.%Y')}")
    st.write(f"**Abreise:** {booking_request['end_date'].strftime('%d.%m.%Y')}")
    st.write(f"**Gäste:** {booking_request['guests']}")

    if booking_request["notes"]:
        st.write(f"**Notizen:** {booking_request['notes']}")

    processing_key = "creating_booking"
    is_processing = st.session_state.get(processing_key, False)

    col_cancel, col_confirm = st.columns(2)

    with col_cancel:
        if st.button(
            "Abbrechen",
            disabled=is_processing,
            use_container_width=True,
        ):
            st.session_state.pop("pending_booking_request", None)
            st.session_state["active_view"] = "agent"
            st.rerun()

    with col_confirm:
        if st.button(
            "Buchung verbindlich erstellen",
            type="primary",
            disabled=is_processing,
            use_container_width=True,
        ):
            st.session_state[processing_key] = True

            with st.spinner("Buchung wird erstellt..."):
                result = create_booking(
                    guest_name=booking_request["guest_name"],
                    guest_email=booking_request["guest_email"],
                    start_date=booking_request["start_date"],
                    end_date=booking_request["end_date"],
                    guests=booking_request["guests"],
                    notes=booking_request["notes"],
                    created_by=booking_request["created_by"],
                )

            if not result["success"]:
                st.session_state[processing_key] = False
                st.error(result["message"])
                return

            st.session_state.pop("pending_booking_request", None)
            st.session_state["last_created_booking"] = result["booking"]

            st.session_state.pop("pending_booking_request", None)
            st.session_state["last_created_booking"] = result["booking"]

            booking = result["booking"]
            st.session_state.setdefault("agent_messages", [])
            st.session_state["agent_messages"].append(
                {
                    "role": "assistant",
                    "content": (
                        "✅ Die Buchung wurde erfolgreich erstellt.\n\n"
                        f"**Buchungs-ID:** {booking['booking_id']}\n\n"
                        f"**Zeitraum:** {booking['start_date']} bis {booking['end_date']}\n\n"
                        f"**Gäste:** {booking['guests']}"
                    ),
                    "artifacts": [],
                }
            )

            with st.spinner("Bestätigungs-E-Mail wird versendet..."):
                try:
                    email_result = send_booking_confirmation_email(result["booking"])
                    set_booking_email_status(
                        success_key="last_booking_email_sent",
                        message_key="last_booking_email_message",
                        email_result=email_result,
                        success_message="Bestätigungs-E-Mail wurde versendet.",
                        failure_message="Bestätigungs-E-Mail konnte nicht versendet werden.",
                    )

                except Exception as exc:
                    st.session_state["last_booking_email_sent"] = False
                    st.session_state["last_booking_email_message"] = str(exc)

            today = date.today()
            tomorrow = today + timedelta(days=1)

            st.session_state["create_start_date"] = today
            st.session_state["create_end_date"] = tomorrow
            st.session_state[processing_key] = False
            st.session_state["active_view"] = "agent"
            #st.session_state["selected_main_tab"] = "Agent"

            st.rerun()

@st.dialog("Buchung erfolgreich erstellt")
def booking_success_dialog() -> None:
    booking = st.session_state.get("last_created_booking")

    if not booking:
        return

    st.success("Die Buchung wurde erfolgreich erstellt.")

    st.write(f"**Buchungs-ID:** {booking['booking_id']}")
    st.write(f"**Name:** {booking['guest_name']}")
    st.write(f"**E-Mail:** {booking['guest_email']}")
    st.write(f"**Anreise:** {booking['start_date']}")
    st.write(f"**Abreise:** {booking['end_date']}")
    st.write(f"**Gäste:** {booking['guests']}")

    if booking.get("notes"):
        st.write(f"**Notizen:** {booking['notes']}")

    if st.session_state.get("last_booking_email_sent"):
        st.success(
            st.session_state.get(
                "last_booking_email_message",
                "Bestätigungs-E-Mail wurde versendet.",
            )
        )
    else:
        st.warning(
            st.session_state.get(
                "last_booking_email_message",
                "Bestätigungs-E-Mail konnte nicht versendet werden.",
            )
        )

    if st.button("OK", type="primary", use_container_width=True):
        st.session_state.pop("last_created_booking", None)
        st.session_state.pop("last_booking_email_sent", None)
        st.session_state.pop("last_booking_email_message", None)
        st.rerun()

@st.dialog("Stornierung bestätigen")
def confirm_cancellation_dialog(user: dict) -> None:
    booking = st.session_state.get("pending_cancellation_booking")

    if not booking:
        st.warning("Es wurde keine Buchung zur Stornierung ausgewählt.")
        return

    st.warning("Bitte bestätige, dass du diese Buchung wirklich stornieren möchtest.")

    st.write(f"**Buchungs-ID:** {booking['booking_id']}")
    st.write(f"**Gast:** {booking['guest_name']}")
    st.write(f"**E-Mail:** {booking['guest_email']}")
    st.write(f"**Anreise:** {booking['start_date']}")
    st.write(f"**Abreise:** {booking['end_date']}")
    st.write(f"**Gäste:** {booking['guests']}")

    processing_key = f"confirm_cancelling_booking_{booking['booking_id']}"
    is_processing = st.session_state.get(processing_key, False)

    col_cancel, col_confirm = st.columns(2)

    with col_cancel:
        if st.button(
            "Abbrechen",
            disabled=is_processing,
            use_container_width=True,
        ):
            st.session_state.pop("pending_cancellation_booking", None)
            st.rerun()

    with col_confirm:
        if st.button(
            "Ja, Buchung stornieren",
            type="primary",
            disabled=is_processing,
            use_container_width=True,
        ):
            st.session_state[processing_key] = True

            with st.spinner("Buchung wird storniert..."):
                result = cancel_booking(
                    booking_id=booking["booking_id"],
                    cancelled_by=user["email"],
                )

            st.session_state[processing_key] = False

            if not result["success"]:
                st.error(result["message"])
                return

            with st.spinner("Stornierungs-E-Mail wird versendet..."):
                try:
                    email_result = send_booking_cancellation_email(result["booking"])
                    set_booking_email_status(
                        success_key="last_cancellation_email_sent",
                        message_key="last_cancellation_email_message",
                        email_result=email_result,
                        success_message="Stornierungs-E-Mail wurde versendet.",
                        failure_message="Stornierungs-E-Mail konnte nicht versendet werden.",
                    )

                except Exception as exc:
                    st.session_state["last_cancellation_email_sent"] = False
                    st.session_state["last_cancellation_email_message"] = str(exc)

            st.session_state.pop("pending_cancellation_booking", None)
            st.session_state["last_cancelled_booking"] = result["booking"]

            booking = result["booking"]
            st.session_state.setdefault("agent_messages", [])
            st.session_state["agent_messages"].append(
                {
                    "role": "assistant",
                    "content": (
                        "✅ Die Buchung wurde erfolgreich storniert.\n\n"
                        f"**Buchungs-ID:** {booking['booking_id']}\n\n"
                        f"**Zeitraum:** {booking['start_date']} bis {booking['end_date']}\n\n"
                        f"**Gast:** {booking['guest_name']}"
                    ),
                    "artifacts": [],
                }
            )
            st.session_state["active_view"] = "agent"
            st.rerun()

@st.dialog("Buchung storniert")
def cancellation_success_dialog() -> None:
    booking = st.session_state.get("last_cancelled_booking")

    if not booking:
        return

    st.success("Die Buchung wurde erfolgreich storniert.")

    st.write(f"**Buchungs-ID:** {booking['booking_id']}")
    st.write(f"**Gast:** {booking['guest_name']}")
    st.write(f"**Anreise:** {booking['start_date']}")
    st.write(f"**Abreise:** {booking['end_date']}")

    if st.session_state.get("last_cancellation_email_sent"):
        st.success(
            st.session_state.get(
                "last_cancellation_email_message",
                "Stornierungs-E-Mail wurde versendet.",
            )
        )
    else:
        st.warning(
            st.session_state.get(
                "last_cancellation_email_message",
                "Stornierungs-E-Mail konnte nicht versendet werden.",
            )
        )

    if st.button("OK", type="primary", width="stretch"):
        st.session_state.pop("last_cancelled_booking", None)
        st.session_state.pop("last_cancellation_email_sent", None)
        st.session_state.pop("last_cancellation_email_message", None)
        st.rerun()

@st.dialog("Buchung bearbeiten")
def edit_booking_dialog() -> None:
    booking = st.session_state.get("editing_booking")

    if not booking:
        st.warning("Es wurde keine Buchung zum Bearbeiten ausgewählt.")
        return

    booking_id = booking["booking_id"]

    st.write("Passe die Buchungsdaten an und speichere die Änderungen.")

    start_date = st.date_input(
        "Anreise",
        value=parse_booking_date(booking["start_date"]),
        min_value=date.today(),
        format="DD.MM.YYYY",
        key=f"edit_start_date_{booking_id}",
    )

    minimum_end_date = start_date + timedelta(days=1)
    current_end_date = parse_booking_date(booking["end_date"])

    if current_end_date <= start_date:
        current_end_date = minimum_end_date

    end_date = st.date_input(
        "Abreise",
        value=current_end_date,
        min_value=minimum_end_date,
        format="DD.MM.YYYY",
        key=f"edit_end_date_{booking_id}",
    )

    guest_name = st.text_input(
        "Name",
        value=booking["guest_name"],
        key=f"edit_guest_name_{booking_id}",
    )

    guest_email = st.text_input(
        "E-Mail",
        value=booking["guest_email"],
        key=f"edit_guest_email_{booking_id}",
    )

    guests = st.number_input(
        "Gäste",
        min_value=1,
        max_value=20,
        value=int(booking["guests"]),
        key=f"edit_guests_{booking_id}",
    )

    notes = st.text_area(
        "Notizen",
        value=booking["notes"],
        key=f"edit_notes_{booking_id}",
    )

    processing_key = f"updating_booking_{booking_id}"
    is_processing = st.session_state.get(processing_key, False)

    col_cancel, col_save = st.columns(2)

    with col_cancel:
        if st.button(
            "Abbrechen",
            disabled=is_processing,
            width="stretch",
        ):
            st.session_state.pop("editing_booking", None)
            st.rerun()

    with col_save:
        if st.button(
            "Änderungen speichern",
            type="primary",
            disabled=is_processing,
            width="stretch",
        ):
            st.session_state[processing_key] = True

            with st.spinner("Buchung wird aktualisiert..."):
                result = update_booking(
                    booking_id=booking_id,
                    guest_name=guest_name,
                    guest_email=guest_email,
                    start_date=start_date,
                    end_date=end_date,
                    guests=int(guests),
                    notes=notes,
                )

            st.session_state[processing_key] = False

            if result["success"]:
                st.session_state.pop("editing_booking", None)
                st.session_state["last_updated_booking"] = result["booking"]

                with st.spinner("Änderungs-E-Mail wird versendet..."):
                    try:
                        email_result = send_booking_update_email(result["booking"])
                        set_booking_email_status(
                            success_key="last_update_email_sent",
                            message_key="last_update_email_message",
                            email_result=email_result,
                            success_message="Änderungs-E-Mail wurde versendet.",
                            failure_message="Änderungs-E-Mail konnte nicht versendet werden.",
                        )

                    except Exception as exc:
                        st.session_state["last_update_email_sent"] = False
                        st.session_state["last_update_email_message"] = str(exc)

                st.success(result["message"])
                st.rerun()

            st.error(result["message"])

            if result.get("conflicts"):
                st.write("Konflikte:")
                st.dataframe(result["conflicts"], width="stretch")
