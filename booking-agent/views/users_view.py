import streamlit as st

from users import (
    ROLE_LABELS,
    ROLE_USER_FAMILIE,
    ROLE_USER_FREUND,
    ROLE_USER_STANDARD,
    create_invited_user,
    disable_user,
    list_users,
    resend_invite,
)


def render_create_user_section(user: dict) -> None:
    st.markdown("### Neuen Benutzer einladen")

    role_options = {
        "Standard": ROLE_USER_STANDARD,
        "Freunde": ROLE_USER_FREUND,
        "Familie": ROLE_USER_FAMILIE,
    }

    with st.form("create_user_form"):
        display_name = st.text_input("Name")
        email = st.text_input("E-Mail")
        role_label = st.selectbox("Rolle", options=list(role_options.keys()))
        notes = st.text_area("Notizen")

        submitted = st.form_submit_button("Benutzer erstellen")

    if not submitted:
        return

    result = create_invited_user(
        email=email,
        display_name=display_name,
        role=role_options[role_label],
        invited_by=user["email"],
        notes=notes,
    )

    if not result["success"]:
        st.error(result["message"])
        return

    st.success(result["message"])

    email_result = result.get("email")

    if email_result and email_result.get("success"):
        st.success("Einladungs-E-Mail wurde versendet.")
    else:
        st.warning("User wurde erstellt, aber die E-Mail konnte nicht gesendet werden.")
        if email_result:
            st.caption(email_result.get("message", ""))

    st.info("Temporäres Passwort wird einmalig angezeigt.")

    temporary_password = result.get("temporary_password")

    if temporary_password:
        st.code(temporary_password, language="text")
    else:
        st.caption("Kein temporäres Passwort im Ergebnis vorhanden.")

    st.json(result["user"])


def render_user_list_section() -> None:
    st.markdown("### Benutzerliste")

    include_disabled_users = st.checkbox("Deaktivierte Benutzer anzeigen", value=True)

    if not st.button("Benutzerliste laden"):
        return

    try:
        with st.spinner("Benutzer werden geladen..."):
            users = list_users(include_disabled=include_disabled_users)

        visible_users = [
            {
                "email": item["email"],
                "display_name": item["display_name"],
                "role": ROLE_LABELS.get(item["role"], item["role"]),
                "status": item["status"],
                "must_change_password": item["must_change_password"],
                "created_at": item["created_at"],
                "last_login_at": item["last_login_at"],
                "last_invite_sent_at": item["last_invite_sent_at"],
                "disabled_at": item["disabled_at"],
                "notes": item["notes"],
            }
            for item in users
        ]

        st.dataframe(visible_users, width="stretch")

    except Exception as exc:
        st.error("Benutzer konnten nicht geladen werden.")
        st.exception(exc)


def render_resend_invite_section(user: dict) -> None:
    st.markdown("### Einladung erneut generieren")

    resend_email = st.text_input("E-Mail für neue Einladung")

    if not st.button("Einladung neu generieren"):
        return

    result = resend_invite(
        email=resend_email,
        invited_by=user["email"],
    )

    if not result["success"]:
        st.error(result["message"])
        return

    st.success(result["message"])

    email_result = result.get("email")

    if email_result and email_result.get("success"):
        st.success("Einladungs-E-Mail wurde versendet.")
    else:
        st.warning("Einladung wurde neu generiert, aber die E-Mail konnte nicht gesendet werden.")
        if email_result:
            st.caption(email_result.get("message", ""))

    st.info("Neues temporäres Passwort wird einmalig angezeigt.")

    temporary_password = result.get("temporary_password")

    if temporary_password:
        st.code(temporary_password, language="text")
    else:
        st.caption("Kein temporäres Passwort im Ergebnis vorhanden.")


def render_disable_user_section(user: dict) -> None:
    st.markdown("### Benutzer deaktivieren")

    disable_email = st.text_input("E-Mail deaktivieren")

    if not st.button("Benutzer deaktivieren"):
        return

    result = disable_user(
        email=disable_email,
        disabled_by=user["email"],
    )

    if result["success"]:
        st.success(result["message"])
    else:
        st.error(result["message"])


def render_users_view(user: dict) -> None:
    st.subheader("Benutzer")

    render_create_user_section(user)

    st.divider()
    render_user_list_section()

    st.divider()
    render_resend_invite_section(user)

    st.divider()
    render_disable_user_section(user)