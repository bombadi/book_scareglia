import streamlit as st
import streamlit.components.v1 as components
from streamlit_calendar import calendar

from calendar_browser import get_calendar_options
from mailer import send_html_report_email


def render_artifact(artifact: dict) -> None:
    artifact_type = artifact.get("type")

    if artifact_type == "booking_list":
        render_booking_list(artifact)
    elif artifact_type == "booking_calendar":
        render_booking_calendar(artifact)
    elif artifact_type == "availability_result":
        render_availability_result(artifact)
    elif artifact_type == "cancellation_status":
        render_cancellation_status(artifact)
    elif artifact_type == "html_report":
        render_html_report(artifact)
    elif artifact_type == "booking_confirmation_required":
        return
    elif artifact_type == "external_link":
        render_external_link(artifact)
    else:
        st.json(artifact)

def render_booking_list(artifact: dict) -> None:
    title = artifact.get("title", "Buchungen")
    data = artifact.get("data", [])

    st.markdown(f"#### {title}")

    if not data:
        st.info("Keine Buchungen gefunden.")
        return

    st.dataframe(data, width="stretch")

def render_booking_calendar(artifact: dict) -> None:
    title = artifact.get("title", "Buchungskalender")
    events = artifact.get("events", [])

    st.markdown(f"#### {title}")

    calendar(
        events=events,
        options=get_calendar_options(),
        key=artifact.get("key", "agent_booking_calendar"),
    )

def render_availability_result(artifact: dict) -> None:
    title = artifact.get("title", "Verfügbarkeit")
    data = artifact.get("data", {})

    st.markdown(f"#### {title}")

    if data.get("available"):
        st.success(data.get("message", "Der Zeitraum ist verfügbar."))
    else:
        st.error(data.get("message", "Der Zeitraum ist nicht verfügbar."))

    periods = data.get("periods", [])

    if periods:
        st.write("Freie Termine:")
        st.dataframe(
            [
                {
                    "Anreise": period.get("start_date", ""),
                    "Abreise": period.get("end_date", ""),
                }
                for period in periods
            ],
            width="stretch",
        )

    conflicts = data.get("conflicts", [])

    if conflicts:
        st.write("Konflikte:")
        st.dataframe(conflicts, width="stretch")

def render_cancellation_status(artifact: dict) -> None:
    title = artifact.get("title", "Stornierbarkeit")
    data = artifact.get("data", {})

    st.markdown(f"#### {title}")

    if data.get("allowed"):
        st.success(data.get("message", "Stornierung möglich."))
    else:
        st.warning(data.get("message", "Stornierung nicht möglich."))

    booking = data.get("booking")

    if not booking:
        return

    st.markdown(
        f"""
    **Buchungs-ID:** {booking.get("booking_id", "-")}  
    **Gast:** {booking.get("guest_name", "-")}  
    **Anreise:** {booking.get("start_date", "-")}  
    **Abreise:** {booking.get("end_date", "-")}  
    **Gäste:** {booking.get("guests", "-")}  
    **Status:** {booking.get("status", "-")}
    """
    )

    if not data.get("allowed"):
        return

    if st.button(
            "Buchung stornieren",
            key=f"cancel_from_agent_{booking.get('booking_id', '')}",
            type="primary",
            width="stretch",
    ):
        st.session_state["pending_cancellation_booking"] = booking
        st.rerun()

def render_html_report(artifact: dict) -> None:
    title = artifact.get("title", "Report")
    html = artifact.get("html", "")
    email_subject = artifact.get("email_subject", title)
    artifact_key = artifact.get("artifact_id") or str(abs(hash(f"{title}-{html[:80]}")))

    st.markdown(f"#### {title}")

    if not html:
        st.warning("Der Report enthält keinen Inhalt.")
        return

    components.html(
        html,
        height=900,
        scrolling=True,
    )

    sources = artifact.get("sources", [])
    reflection = artifact.get("reflection", {})
    initial_queries = artifact.get("initial_queries", [])
    additional_queries = artifact.get("additional_queries", [])

    if sources or reflection or initial_queries or additional_queries:
        with st.expander("Recherche-Details"):
            if initial_queries:
                st.write("Initiale Suchanfragen:")
                st.json(initial_queries)

            if additional_queries:
                st.write("Zusätzliche Suchanfragen nach Reflection:")
                st.json(additional_queries)

            if reflection:
                st.write("Reflection:")
                st.json(reflection)

            if sources:
                st.write("Quellen:")
                st.dataframe(
                    [
                        {
                            "Titel": source.get("title", ""),
                            "URL": source.get("url", ""),
                            "Suchanfrage": source.get("query", ""),
                        }
                        for source in sources
                    ],
                    width="stretch",
                )

    with st.expander("Report per E-Mail versenden"):
        default_email = st.session_state.get("user", {}).get("email", "")
        to_email = st.text_input(
            "Empfänger-E-Mail",
            value=default_email,
            key=f"report_email_{artifact_key}",
        )

        if st.button(
            "Report per E-Mail senden",
            key=f"send_report_email_{artifact_key}",
            width="stretch",
        ):
            try:
                with st.spinner("Report wird per E-Mail versendet..."):
                    result = send_html_report_email(
                        to_email=to_email,
                        subject=email_subject,
                        html_report=html,
                    )

                if result.get("success"):
                    st.success("Report wurde per E-Mail versendet.")
                else:
                    st.warning("Report konnte nicht per E-Mail versendet werden.")

            except Exception as exc:
                st.error("Report konnte nicht per E-Mail versendet werden.")
                st.exception(exc)

def render_external_link(artifact: dict) -> None:
    title = artifact.get("title", "Link")
    url = artifact.get("url", "")
    label = artifact.get("label", "Öffnen")

    st.markdown(f"#### {title}")

    if not url:
        st.warning("Kein Link vorhanden.")
        return

    st.link_button(
        label,
        url,
        width="stretch",
    )