import streamlit as st

from auth import logout_button


def render_sidebar(user: dict) -> None:
    st.sidebar.write(f"👤 {user['name']}")
    st.sidebar.caption(user["email"])

    with st.sidebar.expander("Profil", expanded=False):
        if st.button("Profil bearbeiten", use_container_width=True):
            st.session_state["active_view"] = "profile"
            st.rerun()

        if st.button("Passwort ändern", use_container_width=True):
            st.session_state["active_view"] = "password"
            st.rerun()

        if st.button("History / Memory", use_container_width=True):
            st.session_state["active_view"] = "memory"
            st.rerun()

    if st.sidebar.button("Meine Buchungen", use_container_width=True):
        st.session_state["active_view"] = "my_bookings"
        st.rerun()

    if st.sidebar.button("💬 Agent öffnen", use_container_width=True):
        st.session_state["active_view"] = "agent"
        st.rerun()

    logout_button()