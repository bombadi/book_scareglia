from datetime import date, timedelta

import streamlit as st
from booking_dialogs import confirm_booking_dialog, booking_success_dialog
from bookings import check_availability


def render_create_booking_view(user: dict) -> None:
    st.subheader("Neue Buchung erstellen")

    today = date.today()
    tomorrow = today + timedelta(days=1)

    if st.session_state.get("pending_booking_request"):
        confirm_booking_dialog(user=user)

    if st.session_state.get("last_created_booking"):
        booking_success_dialog()

    if "create_start_date" not in st.session_state:
        st.session_state["create_start_date"] = today

    if "create_end_date" not in st.session_state:
        st.session_state["create_end_date"] = tomorrow

    start_date = st.date_input(
        "Anreise",
        min_value=today,
        format="DD.MM.YYYY",
        key="create_start_date",
    )

    minimum_end_date = start_date + timedelta(days=1)

    if st.session_state["create_end_date"] <= start_date:
        st.session_state["create_end_date"] = minimum_end_date

    end_date = st.date_input(
        "Abreise",
        min_value=minimum_end_date,
        format="DD.MM.YYYY",
        key="create_end_date",
    )

    guest_name = st.text_input(
        "Name",
        value=user.get("name", ""),
    )

    guest_email = st.text_input(
        "E-Mail",
        value=user.get("email", ""),
    )

    guests = st.number_input("Gäste", min_value=1, max_value=20, value=2)
    notes = st.text_area("Notizen")

    st.caption(f"Erstellt von: {user['email']}")

    submitted = st.button(
        "Verfügbarkeit prüfen und buchen",
        type="primary",
        disabled=st.session_state.get("creating_booking", False),
    )

    if submitted:
        try:
            with st.spinner("Verfügbarkeit wird geprüft..."):
                availability = check_availability(start_date, end_date)

            if not availability["available"]:
                st.error(availability["message"])

                if availability["conflicts"]:
                    st.write("Konflikte:")
                    st.dataframe(availability["conflicts"], width="stretch")

            else:
                st.session_state["pending_booking_request"] = {
                    "guest_name": guest_name,
                    "guest_email": guest_email,
                    "start_date": start_date,
                    "end_date": end_date,
                    "guests": int(guests),
                    "notes": notes,
                    "created_by": user["email"],
                }

                # confirm_booking_dialog(user=user)
                st.rerun()
        except Exception as exc:
            st.error("Buchung konnte nicht geprüft werden.")
            st.exception(exc)