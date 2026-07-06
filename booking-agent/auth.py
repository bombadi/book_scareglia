import streamlit as st

from users import authenticate_user, change_user_password, reset_user_password

import base64

def set_login_background(image_path: str):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>

        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def login_form() -> None:
    set_login_background("assets/login_background.png")

    if "landing_page" not in st.session_state:
        st.session_state["landing_page"] = "login"

    if "show_password_reset" not in st.session_state:
        st.session_state["show_password_reset"] = False

    if "login_status" not in st.session_state:
        st.session_state["login_status"] = None

    st.markdown(
        """
        <style>
        header[data-testid="stHeader"] {
            display: none;
        }

        .block-container {
            padding-top: 1.1rem;
        }

        h1,
        h3 {
            color: #F5F5F2 !important;
        }

        div[data-testid="stTextInput"] label[data-testid="stWidgetLabel"] p {
            color: #F5F5F2 !important;
            font-weight: 500;
        }

        /* normale Menübuttons */
        div[data-testid="stButton"] button[kind="tertiary"] {
            border: none;
            background: transparent;
            padding: 0;
            color: #F5F5F2;
            font-weight: 500;
            white-space: nowrap;
        }

        div[data-testid="stButton"] button[kind="tertiary"]:hover {
            color: white;
            text-decoration: underline;
            background: transparent;
        }

        /* Login-Menübutton */
        div[data-testid="stHorizontalBlock"] > div:last-child
        div[data-testid="stButton"] button[kind="tertiary"] {
            border: 1px solid rgba(255,255,255,0.65);
            border-radius: 999px;
            padding: 6px 18px;
            text-decoration: none;
            background: transparent;
        }

        div[data-testid="stHorizontalBlock"] > div:last-child
        div[data-testid="stButton"] button[kind="tertiary"]:hover {
            background: rgba(255,255,255,0.16);
            border-color: rgba(255,255,255,0.9);
            color: white;
            text-decoration: none;
        }

        div[data-testid="stFormSubmitButton"] button {
            width: 100% !important;
            background: #2E7D32 !important;
            color: white !important;
            border: 1px solid #2E7D32 !important;
            border-radius: 10px !important;
            font-weight: 600;
            height: 46px;
        }

        div[data-testid="stFormSubmitButton"] button:hover {
            background: #388E3C !important;
            border-color: #4CAF50 !important;
            color: white !important;
            box-shadow: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    nav_left, nav_gallery, nav_house, nav_contact, nav_spacer, nav_login = st.columns(
        [9.0, 0.7, 0.9, 0.7, 0.7, 0.8]
    )

    with nav_gallery:
        if st.button("Galerie", type="tertiary", key="nav_gallery"):
            st.session_state["landing_page"] = "gallery"
            st.session_state["login_status"] = None
            st.rerun()

    with nav_house:
        if st.button("Ferienhaus", type="tertiary", key="nav_house"):
            st.session_state["landing_page"] = "house"
            st.session_state["login_status"] = None
            st.rerun()

    with nav_contact:
        if st.button("Kontakt", type="tertiary", key="nav_contact"):
            st.session_state["landing_page"] = "contact"
            st.session_state["login_status"] = None
            st.rerun()

    with nav_login:
        if st.button("Login", type="tertiary", key="nav_login"):
            st.session_state["landing_page"] = "login"
            st.session_state["login_status"] = None
            st.rerun()

    page = st.session_state["landing_page"]

    if page == "gallery":
        st.markdown(
            "<h1 style='text-align:center;'>Galerie</h1>",
            unsafe_allow_html=True,
        )
        st.info("Hier kannst du später Bilder des Ferienhauses anzeigen.")
        return

    if page == "house":
        st.markdown(
            "<h1 style='text-align:center;'>Ferienhaus</h1>",
            unsafe_allow_html=True,
        )
        st.info("Hier kannst du später Informationen zum Ferienhaus anzeigen.")
        return

    if page == "contact":
        st.markdown(
            "<h1 style='text-align:center;'>Kontakt</h1>",
            unsafe_allow_html=True,
        )
        st.info("Hier kannst du später Kontaktinformationen oder ein Formular anzeigen.")
        return

    st.markdown(
        "<h1 style='text-align:center;'>Buche deinen Urlaub</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='text-align:center; color:#E5E7EB;'>Bitte melde dich an, um fortzufahren.</p>",
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 0.9, 1])

    with center:
        with st.form(
            "login_form",
            clear_on_submit=False,
            border=False,
        ):
            email = st.text_input(
                "E-Mail",
                key="login_email",
                placeholder="name@beispiel.ch",
            )

            password = st.text_input(
                "Passwort",
                type="password",
                key="login_password",
            )

            submitted = st.form_submit_button(
                "Einloggen",
                width="stretch",
            )

        if submitted:
            result = authenticate_user(
                email=email,
                password=password,
            )

            if result["success"]:
                st.session_state["login_status"] = {
                    "type": "success",
                    "message": "Login erfolgreich. Du wirst weitergeleitet...",
                }

                st.session_state["authenticated"] = True
                st.session_state["user"] = result["user"]
                st.session_state["show_password_reset"] = False
                st.rerun()

            st.session_state["login_status"] = {
                "type": "error",
                "message": "Fehlgeschlagen. Prüfe deine Eingaben.",
            }

        if not st.session_state["show_password_reset"]:
            _, link, _ = st.columns([1, 1.2, 1])

            with link:
                if st.button(
                    "Passwort vergessen?",
                    type="tertiary",
                    width="stretch",
                    key="forgot_password_link",
                ):
                    st.session_state["show_password_reset"] = True
                    st.session_state["login_status"] = None
                    st.rerun()

        if st.session_state["show_password_reset"]:
            with st.form(
                "password_reset_form",
                clear_on_submit=False,
                border=False,
            ):
                reset_email = st.text_input(
                    "E-Mail für Passwort-Reset",
                    value=st.session_state.get("login_email", ""),
                    key="reset_email",
                )

                reset_submitted = st.form_submit_button(
                    "Temporäres Passwort senden",
                    width="stretch",
                )

            if reset_submitted:
                reset_user_password(email=reset_email)

                st.session_state["login_status"] = {
                    "type": "success",
                    "message": (
                        "Falls ein Konto mit dieser E-Mail existiert, "
                        "wurde ein temporäres Passwort versendet."
                    ),
                }

                st.session_state["show_password_reset"] = False
                st.rerun()

        status = st.session_state.get("login_status")

        if status is not None:
            if status["type"] == "info":
                st.info(status["message"])
            elif status["type"] == "success":
                st.success(status["message"])
            elif status["type"] == "error":
                st.error(status["message"])

def require_login() -> None:
    if st.session_state.get("authenticated"):
        return

    login_form()
    st.stop()


def get_current_user() -> dict:
    return st.session_state.get(
        "user",
        {
            "user_id": "",
            "email": "",
            "name": "",
            "role": "",
            "status": "",
            "must_change_password": False,
        },
    )

def change_password_form(force_change: bool = False) -> None:
    user = get_current_user()

    if force_change:
        st.title("Passwort ändern")
        st.warning("Bitte ändere dein temporäres Passwort, bevor du fortfährst.")
    else:
        st.subheader("Passwort ändern")

    with st.form("change_password_form"):
        if force_change:
            current_password = None
        else:
            current_password = st.text_input("Aktuelles Passwort", type="password")

        new_password = st.text_input("Neues Passwort", type="password")
        new_password_repeat = st.text_input("Neues Passwort wiederholen", type="password")

        submitted = st.form_submit_button("Passwort ändern")

    if not submitted:
        return

    if not new_password:
        st.error("Bitte gib ein neues Passwort ein.")
        return

    if new_password != new_password_repeat:
        st.error("Die neuen Passwörter stimmen nicht überein.")
        return

    result = change_user_password(
        email=user["email"],
        current_password=current_password,
        new_password=new_password,
        require_current_password=not force_change,
    )

    if not result["success"]:
        st.error(result["message"])
        return

    st.session_state["user"] = result["user"]
    st.session_state["authenticated"] = True

    st.success(result["message"])
    st.rerun()


def require_password_change_if_needed() -> None:
    user = get_current_user()

    if not user.get("must_change_password"):
        return

    change_password_form(force_change=True)
    st.stop()


def logout_button() -> None:
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

def forgot_password_form() -> None:
    st.subheader("Passwort vergessen")

    with st.form("forgot_password_form"):
        email = st.text_input("E-Mail")
        submitted = st.form_submit_button("Temporäres Passwort erstellen")

    if not submitted:
        return

    if not email:
        st.error("Bitte gib deine E-Mail-Adresse ein.")
        return

    result = create_password_reset(email=email)

    if not result["success"]:
        st.error(result["message"])
        return

    st.success(result["message"])