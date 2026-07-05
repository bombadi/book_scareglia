import streamlit as st

from auth import change_password_form
from users import update_user_memory, update_user_profile


def render_profile_view(user: dict) -> None:
    st.subheader("Profil bearbeiten")

    with st.form("profile_form"):
        st.text_input("E-Mail", value=user["email"], disabled=True)

        display_name = st.text_input(
            "Name",
            value=user.get("name", ""),
        )

        interests = st.text_area(
            "Interessen",
            value=user.get("interests", ""),
            help="Zum Beispiel: Wandern, Ruhe, gutes Essen, familienfreundliche Aktivitäten.",
        )

        submitted = st.form_submit_button("Profil speichern")

    if submitted:
        result = update_user_profile(
            email=user["email"],
            display_name=display_name,
            interests=interests,
        )

        if result["success"]:
            st.session_state["user"] = result["user"]
            st.success(result["message"])
            st.rerun()

        st.error(result["message"])


def render_password_view() -> None:
    st.subheader("Passwort ändern")

    change_password_form(force_change=False)


def render_memory_view(user: dict) -> None:
    st.subheader("History / Memory")

    st.write(
        "Hier kannst du steuern, welche Informationen der Agent über deine Wünsche "
        "und laufenden Themen berücksichtigen soll."
    )

    with st.form("memory_form"):
        longterm = st.text_area(
            "Longterm Memory",
            value=user.get("longterm", ""),
            help="Dauerhafte Informationen, die längerfristig gelten.",
        )

        midterm = st.text_area(
            "Midterm Memory",
            value=user.get("midterm", ""),
            help="Informationen, die für die nächsten Wochen oder Monate relevant sind.",
        )

        shortterm = st.text_area(
            "Shortterm Memory",
            value=user.get("shortterm", ""),
            help="Aktuelle Hinweise oder kurzfristige Wünsche.",
        )

        submitted = st.form_submit_button("History / Memory speichern")

    if submitted:
        result = update_user_memory(
            email=user["email"],
            longterm=longterm,
            midterm=midterm,
            shortterm=shortterm,
        )

        if result["success"]:
            st.session_state["user"] = result["user"]
            st.success(result["message"])
            st.rerun()

        st.error(result["message"])