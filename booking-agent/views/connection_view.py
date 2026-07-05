import streamlit as st

from google_sheets import test_connection


def render_connection_view() -> None:
    st.subheader("Verbindung testen")

    if st.button("Google Sheets Verbindung testen"):
        try:
            with st.spinner("Verbindung wird getestet..."):
                result = test_connection()

            st.success("Verbindung erfolgreich.")
            st.json(result)

        except Exception as exc:
            st.error("Verbindung fehlgeschlagen.")
            st.exception(exc)