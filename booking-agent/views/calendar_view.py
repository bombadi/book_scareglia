import streamlit as st
from calendar_browser import get_booking_calendar_events, get_calendar_options
from streamlit_calendar import calendar


def render_calendar_view() -> None:
    st.subheader("Buchungskalender")

    st.markdown(
        """
        <style>
        .fc {
            font-size: 0.86rem;
        }

        .fc .fc-toolbar-title {
            font-size: 1.25rem;
        }

        .fc .fc-daygrid-day-frame {
            min-height: 72px;
        }

        .fc .fc-daygrid-event {
            font-size: 0.75rem;
            padding: 1px 4px;
            border-radius: 4px;
        }

        .booking-event-cancelled {
            opacity: 0.72;
            text-decoration: line-through;
            border-style: dashed !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    include_cancelled_calendar = st.checkbox(
        "Stornierte Buchungen im Kalender anzeigen",
        value=False,
    )

    if st.button("Kalender aktualisieren"):
        st.rerun()

    try:
        events = get_booking_calendar_events(
            include_cancelled=include_cancelled_calendar,
        )

        calendar_result = calendar(
            events=events,
            options=get_calendar_options(),
            key="booking_calendar",
        )

        selected_event = calendar_result.get("eventClick")

        if selected_event:
            event = selected_event.get("event", {})
            props = event.get("extendedProps", {})

            st.markdown("### Buchungsdetails")
            st.write(f"**Buchungs-ID:** {props.get('booking_id', '')}")
            st.write(f"**Status:** {props.get('status', '')}")
            st.write(f"**Gast:** {props.get('guest_name', '')}")
            st.write(f"**E-Mail:** {props.get('guest_email', '')}")
            st.write(f"**Gäste:** {props.get('guests', '')}")
            st.write(f"**Anreise:** {props.get('start_date', '')}")
            st.write(f"**Abreise:** {props.get('end_date', '')}")
            st.write(f"**Erstellt von:** {props.get('created_by', '')}")
            st.write(f"**Erstellt am:** {props.get('created_at', '')}")

            notes = props.get("notes", "")
            if notes:
                st.write(f"**Notizen:** {notes}")

    except Exception as exc:
        st.error("Kalender konnte nicht geladen werden.")
        st.exception(exc)