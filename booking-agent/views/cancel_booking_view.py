import streamlit as st

from booking_dialogs import confirm_cancellation_dialog
from bookings import get_cancellation_status


def render_cancel_booking_view(user: dict) -> None:
    st.subheader("Buchung stornieren")

    booking_id = st.text_input("Buchungs-ID")

    st.caption(f"Storniert von: {user['email']}")

    if st.button("Stornierbarkeit prüfen"):
        try:
            with st.spinner("Stornierbarkeit wird geprüft..."):
                result = get_cancellation_status(booking_id)

            if result["success"] and result["allowed"]:
                st.success(result["message"])
                st.write("Buchung:")
                st.json(result["booking"])

            elif result["success"] and not result["allowed"]:
                st.warning(result["message"])

                if result["booking"]:
                    st.write("Buchung:")
                    st.json(result["booking"])

            else:
                st.error(result["message"])

        except Exception as exc:
            st.error("Stornierbarkeit konnte nicht geprüft werden.")
            st.exception(exc)

    cancel_form_processing_key = "cancelling_booking_from_tab"
    is_cancel_form_processing = st.session_state.get(cancel_form_processing_key, False)

    if st.button(
        "Buchung stornieren",
        disabled=is_cancel_form_processing,
    ):
        try:
            with st.spinner("Buchung wird geladen..."):
                cancellation_status = get_cancellation_status(booking_id)

            if not cancellation_status["success"]:
                st.error(cancellation_status["message"])

            elif not cancellation_status["allowed"]:
                st.warning(cancellation_status["message"])

            else:
                st.session_state["pending_cancellation_booking"] = cancellation_status["booking"]
                confirm_cancellation_dialog(user=user)

        except Exception as exc:
            st.error("Stornierung konnte nicht vorbereitet werden.")
            st.exception(exc)