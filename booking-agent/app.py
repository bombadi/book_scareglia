import streamlit as st

from auth import (
    get_current_user,
    require_login,
    require_password_change_if_needed,
)
from layout import render_sidebar
from views.agent_view import render_agent_view
from views.bookings_view import render_bookings_view
from views.calendar_view import render_calendar_view
from views.cancel_booking_view import render_cancel_booking_view
from views.connection_view import render_connection_view
from views.create_booking_view import render_create_booking_view
from views.my_bookings_view import render_my_bookings_view
from views.profile_view import (
    render_memory_view,
    render_password_view,
    render_profile_view,
)
from views.users_view import render_users_view

st.set_page_config(
    page_title="Ferienhaus Agent",
    page_icon="🏡",
    layout="wide",
)

require_login()
require_password_change_if_needed()

user = get_current_user()

if "active_view" not in st.session_state:
    st.session_state["active_view"] = "agent"

render_sidebar(user)

st.title("🏡 Ferienhaus Agent")

if st.session_state["active_view"] == "profile":
    render_profile_view(user)
    st.stop()

if st.session_state["active_view"] == "password":
    render_password_view()
    st.stop()

if st.session_state["active_view"] == "memory":
    render_memory_view(user)
    st.stop()

if st.session_state["active_view"] == "my_bookings":
    render_my_bookings_view(user)
    st.stop()

if st.session_state["active_view"] == "create_booking":
    render_create_booking_view(user)
    st.stop()

tabs = [
    "Agent",
    "Kalender",
    "Buchungen",
    "Neue Buchung",
    "Stornieren",
    "Verbindung",
]

if user["role"] == "admin":
    tabs.append("Benutzer")

if "selected_main_tab" not in st.session_state:
    st.session_state["selected_main_tab"] = "Agent"

if st.session_state["selected_main_tab"] not in tabs:
    st.session_state["selected_main_tab"] = "Agent"

selected_main_tab = st.radio(
    "Navigation",
    options=tabs,
    horizontal=True,
    key="selected_main_tab",
    label_visibility="collapsed",
)

if selected_main_tab == "Agent":
    render_agent_view(user)

if selected_main_tab == "Kalender":
    render_calendar_view()

if selected_main_tab == "Buchungen":
    render_bookings_view()

if selected_main_tab == "Neue Buchung":
    render_create_booking_view(user)


if selected_main_tab == "Stornieren":
    render_cancel_booking_view(user)


if selected_main_tab == "Verbindung":
    render_connection_view()

if selected_main_tab == "Benutzer":
    render_users_view(user)