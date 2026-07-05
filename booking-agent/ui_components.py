from datetime import date, datetime
from uuid import uuid4

import streamlit as st


def render_status_badge(status: str) -> None:
    normalized_status = status.strip().lower()

    status_styles = {
        "confirmed": {
            "label": "Bestätigt",
            "background": "#dcfce7",
            "color": "#166534",
            "border": "#86efac",
        },
        "cancelled": {
            "label": "Storniert",
            "background": "#fee2e2",
            "color": "#991b1b",
            "border": "#fecaca",
        },
    }

    style = status_styles.get(
        normalized_status,
        {
            "label": status or "Unbekannt",
            "background": "#fef9c3",
            "color": "#854d0e",
            "border": "#fde68a",
        },
    )

    st.markdown(
        f"""
        <span style="
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            background: {style["background"]};
            color: {style["color"]};
            border: 1px solid {style["border"]};
            font-size: 0.85rem;
            font-weight: 600;
        ">
            {style["label"]}
        </span>
        """,
        unsafe_allow_html=True,
    )


def get_booking_card_prefix(status: str) -> str:
    normalized_status = status.strip().lower()

    if normalized_status == "confirmed":
        return "🟢"

    if normalized_status == "cancelled":
        return "🔴"

    return "🟡"


def parse_booking_date(value: str) -> date:
    return datetime.strptime(value, "%d.%m.%Y").date()


def add_artifact_ids(artifacts: list[dict]) -> list[dict]:
    return [
        {
            **artifact,
            "artifact_id": artifact.get("artifact_id") or f"artifact_{uuid4().hex}",
        }
        for artifact in artifacts
    ]