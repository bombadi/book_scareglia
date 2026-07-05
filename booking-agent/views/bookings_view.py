import streamlit as st

from bookings import list_bookings


def render_bookings_view() -> None:
    st.subheader("Aktuelle Buchungen")

    include_cancelled = st.checkbox("Stornierte Buchungen anzeigen")

    if st.button("Buchungen laden"):
        try:
            bookings = list_bookings(include_cancelled=include_cancelled)
            st.dataframe(bookings, use_container_width=True)

        except Exception as exc:
            st.error("Buchungen konnten nicht geladen werden.")
            st.exception(exc)