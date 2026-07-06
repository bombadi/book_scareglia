import streamlit as st

from auth import logout_button


def render_sidebar(user: dict) -> None:
    st.sidebar.write(f"👤 {user['name']}")
    st.sidebar.caption(user["email"])

    with st.sidebar.expander("Profil", expanded=False):
        if st.button("Profil bearbeiten", width="stretch"):
            st.session_state["active_view"] = "profile"
            st.rerun()

        if st.button("Passwort ändern", width="stretch"):
            st.session_state["active_view"] = "password"
            st.rerun()

        if st.button("History / Memory", width="stretch"):
            st.session_state["active_view"] = "memory"
            st.rerun()

    if st.sidebar.button("Meine Buchungen", width="stretch"):
        st.session_state["active_view"] = "my_bookings"
        st.rerun()

    if st.sidebar.button("💬 Agent öffnen", width="stretch"):
        st.session_state["active_view"] = "agent"
        st.rerun()

    logout_button()