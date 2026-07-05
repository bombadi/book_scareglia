from datetime import date

import streamlit as st
from booking_dialogs import confirm_cancellation_dialog, edit_booking_dialog
from bookings import (
    get_cancellation_action,
    list_bookings_for_user,
)
from ui_components import (
    get_booking_card_prefix,
    parse_booking_date,
    render_status_badge,
)


def render_update_success_message() -> None:
    if "last_updated_booking" not in st.session_state:
        return

    updated_booking = st.session_state["last_updated_booking"]

    st.success(
        f"Die Buchung {updated_booking['booking_id']} wurde aktualisiert."
    )

    if st.session_state.get("last_update_email_sent"):
        st.success(
            st.session_state.get(
                "last_update_email_message",
                "Änderungs-E-Mail wurde versendet.",
            )
        )
    else:
        st.warning(
            st.session_state.get(
                "last_update_email_message",
                "Änderungs-E-Mail konnte nicht versendet werden.",
            )
        )

    if st.button("Update-Meldung ausblenden"):
        st.session_state.pop("last_updated_booking", None)
        st.session_state.pop("last_update_email_sent", None)
        st.session_state.pop("last_update_email_message", None)
        st.rerun()


def split_bookings_by_date(bookings: list[dict]) -> tuple[list[dict], list[dict]]:
    today = date.today()

    future_bookings = []
    past_bookings = []

    for booking in bookings:
        end_date = parse_booking_date(booking["end_date"])

        if end_date >= today:
            future_bookings.append(booking)
        else:
            past_bookings.append(booking)

    future_bookings = sorted(
        future_bookings,
        key=lambda booking: parse_booking_date(booking["start_date"]),
    )

    past_bookings = sorted(
        past_bookings,
        key=lambda booking: parse_booking_date(booking["start_date"]),
        reverse=True,
    )

    return future_bookings, past_bookings


def render_booking_details(booking: dict) -> None:
    st.write(f"**Buchungs-ID:** {booking['booking_id']}")
    st.write(f"**Gast:** {booking['guest_name']}")
    st.write(f"**E-Mail:** {booking['guest_email']}")
    st.write(f"**Anreise:** {booking['start_date']}")
    st.write(f"**Abreise:** {booking['end_date']}")
    st.write(f"**Gäste:** {booking['guests']}")
    st.write("**Status:**")
    render_status_badge(booking["status"])

    if booking["notes"]:
        st.write(f"**Notizen:** {booking['notes']}")


def render_future_booking(booking: dict, user: dict) -> None:
    cancellation_action = get_cancellation_action(booking)
    booking_prefix = get_booking_card_prefix(booking["status"])

    with st.expander(
        f"{booking_prefix} {booking['start_date']} bis {booking['end_date']} · {booking['guest_name']}",
        expanded=False,
    ):
        col_details, col_actions = st.columns([2, 1])

        with col_details:
            render_booking_details(booking)

            if cancellation_action["deadline"]:
                st.caption(
                    f"Stornierung möglich bis: {cancellation_action['deadline']}"
                )
            else:
                st.caption(cancellation_action["message"])

        with col_actions:
            if booking["status"] == "cancelled":
                st.info("Diese Buchung ist storniert.")
                return

            if st.button(
                "Bearbeiten",
                key=f"edit_booking_{booking['booking_id']}",
                disabled=st.session_state.get(
                    f"updating_booking_{booking['booking_id']}",
                    False,
                ),
                width="stretch",
            ):
                st.session_state["editing_booking"] = booking
                edit_booking_dialog()

            cancel_processing_key = f"cancelling_booking_{booking['booking_id']}"
            is_cancelling = st.session_state.get(cancel_processing_key, False)

            if st.button(
                cancellation_action["label"],
                key=f"cancel_booking_{booking['booking_id']}",
                disabled=not cancellation_action["allowed"] or is_cancelling,
                width="stretch",
            ):
                st.session_state["pending_cancellation_booking"] = booking
                confirm_cancellation_dialog(user=user)


def render_past_booking(booking: dict) -> None:
    booking_prefix = get_booking_card_prefix(booking["status"])

    with st.expander(
        f"{booking_prefix} {booking['start_date']} bis {booking['end_date']} · {booking['guest_name']}",
        expanded=False,
    ):
        render_booking_details(booking)


def render_my_bookings_view(user: dict) -> None:
    st.subheader("Meine Buchungen")

    st.write(
        "Hier findest du deine Buchungen. Zukünftige Buchungen kannst du bearbeiten "
        "oder stornieren, sofern die Stornierungsfrist noch nicht abgelaufen ist."
    )

    render_update_success_message()

    include_cancelled_my_bookings = st.checkbox(
        "Stornierte Buchungen anzeigen",
        value=True,
    )

    try:
        my_bookings = list_bookings_for_user(
            user_email=user["email"],
            include_cancelled=include_cancelled_my_bookings,
        )

        if not my_bookings:
            st.info("Du hast aktuell keine Buchungen.")
            return

        future_bookings, past_bookings = split_bookings_by_date(my_bookings)

        if future_bookings:
            st.markdown("### Zukünftige Buchungen")

            for booking in future_bookings:
                render_future_booking(booking, user)
        else:
            st.info("Du hast aktuell keine zukünftigen Buchungen.")

        if past_bookings:
            st.divider()
            st.markdown("### Vergangene Buchungen")

            for booking in past_bookings:
                render_past_booking(booking)

    except Exception as exc:
        st.error("Deine Buchungen konnten nicht geladen werden.")
        st.exception(exc)