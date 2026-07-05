from datetime import date
from random import choice, randint
from uuid import uuid4

import bcrypt
import streamlit as st

from google_sheets import get_worksheet
from mailer import send_invite_email

USERS_WORKSHEET_NAME = "users"
DATE_FORMAT = "%d.%m.%Y"

STATUS_INVITED = "invited"
STATUS_ACTIVE = "active"
STATUS_DISABLED = "disabled"

ROLE_ADMIN = "admin"
ROLE_USER_STANDARD = "user_standard"
ROLE_USER_FREUND = "user_freund"
ROLE_USER_FAMILIE = "user_familie"

ALLOWED_INVITE_ROLES = {
    ROLE_USER_STANDARD,
    ROLE_USER_FREUND,
    ROLE_USER_FAMILIE,
}

ROLE_LABELS = {
    ROLE_USER_STANDARD: "Standard",
    ROLE_USER_FREUND: "Freunde",
    ROLE_USER_FAMILIE: "Familie",
}

TEMP_PASSWORD_WORDS = [
    "Katze",
    "Maus",
    "Tiger",
    "Nase",
    "Auge",
    "Auto",
]


def _today_string() -> str:
    return date.today().strftime(DATE_FORMAT)


def _normalize_bool(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "YES", "1", "JA"}


def _normalize_user(row: dict) -> dict:
    return {
        "user_id": str(row.get("user_id", "")).strip(),
        "email": str(row.get("email", "")).strip().lower(),
        "display_name": str(row.get("display_name", "")).strip(),
        "role": str(row.get("role", "")).strip().lower(),
        "status": str(row.get("status", "")).strip().lower(),
        "password_hash": str(row.get("password_hash", "")).strip(),
        "must_change_password": _normalize_bool(row.get("must_change_password", "")),
        "created_at": str(row.get("created_at", "")).strip(),
        "last_login_at": str(row.get("last_login_at", "")).strip(),
        "invited_at": str(row.get("invited_at", "")).strip(),
        "invited_by": str(row.get("invited_by", "")).strip(),
        "last_invite_sent_at": str(row.get("last_invite_sent_at", "")).strip(),
        "disabled_at": str(row.get("disabled_at", "")).strip(),
        "disabled_by": str(row.get("disabled_by", "")).strip(),
        "notes": str(row.get("notes", "")).strip(),
        "interests": str(row.get("interests", "")).strip(),
        "longterm": str(row.get("longterm", "")).strip(),
        "midterm": str(row.get("midterm", "")).strip(),
        "shortterm": str(row.get("shortterm", "")).strip(),
    }


def _session_user_from_user(user: dict) -> dict:
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["display_name"],
        "role": user["role"],
        "status": user["status"],
        "must_change_password": user["must_change_password"],
        "interests": user.get("interests", ""),
        "longterm": user.get("longterm", ""),
        "midterm": user.get("midterm", ""),
        "shortterm": user.get("shortterm", ""),
    }


def update_user_profile(
    email: str,
    display_name: str,
    interests: str,
) -> dict:
    user = find_user_by_email(email)

    if user is None:
        return {
            "success": False,
            "message": "User wurde nicht gefunden.",
            "user": None,
        }

    if user["status"] == STATUS_DISABLED:
        return {
            "success": False,
            "message": "Dieser User ist deaktiviert.",
            "user": None,
        }

    if not display_name.strip():
        return {
            "success": False,
            "message": "Bitte gib einen Namen ein.",
            "user": None,
        }

    row_index = _get_user_row_index_by_email(email)

    if row_index is None:
        return {
            "success": False,
            "message": "User-Zeile wurde nicht gefunden.",
            "user": None,
        }

    sheet = get_worksheet(USERS_WORKSHEET_NAME)
    sheet.update_cell(row_index, 3, display_name.strip())
    sheet.update_cell(row_index, 16, interests.strip())

    clear_users_cache()

    updated_user = find_user_by_email(email)

    return {
        "success": True,
        "message": "Profil wurde gespeichert.",
        "user": _session_user_from_user(updated_user),
    }


def update_user_memory(
    email: str,
    longterm: str,
    midterm: str,
    shortterm: str,
) -> dict:
    user = find_user_by_email(email)

    if user is None:
        return {
            "success": False,
            "message": "User wurde nicht gefunden.",
            "user": None,
        }

    if user["status"] == STATUS_DISABLED:
        return {
            "success": False,
            "message": "Dieser User ist deaktiviert.",
            "user": None,
        }

    row_index = _get_user_row_index_by_email(email)

    if row_index is None:
        return {
            "success": False,
            "message": "User-Zeile wurde nicht gefunden.",
            "user": None,
        }

    sheet = get_worksheet(USERS_WORKSHEET_NAME)
    sheet.update_cell(row_index, 17, longterm.strip())
    sheet.update_cell(row_index, 18, midterm.strip())
    sheet.update_cell(row_index, 19, shortterm.strip())

    clear_users_cache()

    updated_user = find_user_by_email(email)

    return {
        "success": True,
        "message": "History / Memory wurde gespeichert.",
        "user": _session_user_from_user(updated_user),
    }


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False

    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )

def generate_temporary_password() -> str:
    first_word = choice(TEMP_PASSWORD_WORDS)
    second_word = choice([word for word in TEMP_PASSWORD_WORDS if word != first_word])
    number = randint(100, 999)

    return f"{first_word}{second_word}{number}"

@st.cache_data(ttl=300, show_spinner=False)
def load_users() -> list[dict]:
    sheet = get_worksheet(USERS_WORKSHEET_NAME)
    rows = sheet.get_all_records()
    return [_normalize_user(row) for row in rows]


def clear_users_cache() -> None:
    load_users.clear()

def list_users(include_disabled: bool = True) -> list[dict]:
    users = load_users()

    if include_disabled:
        return users

    return [
        user
        for user in users
        if user["status"] != STATUS_DISABLED
    ]

def find_user_by_email(email: str) -> dict | None:
    normalized_email = email.strip().lower()

    for user in load_users():
        if user["email"] == normalized_email:
            return user

    return None


def _get_user_row_index_by_email(email: str) -> int | None:
    sheet = get_worksheet(USERS_WORKSHEET_NAME)
    rows = sheet.get_all_records()

    normalized_email = email.strip().lower()

    for index, row in enumerate(rows, start=2):
        row_email = str(row.get("email", "")).strip().lower()

        if row_email == normalized_email:
            return index

    return None


def update_last_login(email: str) -> None:
    row_index = _get_user_row_index_by_email(email)

    if row_index is None:
        return

    sheet = get_worksheet(USERS_WORKSHEET_NAME)
    sheet.update_cell(row_index, 9, _today_string())

def change_user_password(
    email: str,
    new_password: str,
    current_password: str | None = None,
    require_current_password: bool = True,
) -> dict:
    user = find_user_by_email(email)

    if user is None:
        return {
            "success": False,
            "error_code": "USER_NOT_FOUND",
            "message": "User wurde nicht gefunden.",
        }

    if user["status"] == STATUS_DISABLED:
        return {
            "success": False,
            "error_code": "USER_DISABLED",
            "message": "Dieser User ist deaktiviert.",
        }

    if require_current_password:
        if not current_password:
            return {
                "success": False,
                "error_code": "MISSING_CURRENT_PASSWORD",
                "message": "Bitte gib dein aktuelles Passwort ein.",
            }

        if not verify_password(current_password, user["password_hash"]):
            return {
                "success": False,
                "error_code": "INVALID_CURRENT_PASSWORD",
                "message": "Das aktuelle Passwort ist nicht korrekt.",
            }

    if len(new_password) < 8:
        return {
            "success": False,
            "error_code": "PASSWORD_TOO_SHORT",
            "message": "Das neue Passwort muss mindestens 8 Zeichen lang sein.",
        }

    row_index = _get_user_row_index_by_email(email)

    if row_index is None:
        return {
            "success": False,
            "error_code": "USER_ROW_NOT_FOUND",
            "message": "User-Zeile wurde nicht gefunden.",
        }

    sheet = get_worksheet(USERS_WORKSHEET_NAME)
    sheet.update_cell(row_index, 5, STATUS_ACTIVE)
    sheet.update_cell(row_index, 6, hash_password(new_password))
    sheet.update_cell(row_index, 7, "FALSE")

    clear_users_cache()

    updated_user = find_user_by_email(email)

    return {
        "success": True,
        "error_code": None,
        "message": "Passwort wurde geändert.",
        "user": _session_user_from_user(updated_user),
    }



def authenticate_user(email: str, password: str) -> dict:
    user = find_user_by_email(email)

    if user is None:
        return {
            "success": False,
            "error_code": "USER_NOT_FOUND",
            "message": "User wurde nicht gefunden.",
            "user": None,
        }

    if user["status"] == STATUS_DISABLED:
        return {
            "success": False,
            "error_code": "USER_DISABLED",
            "message": "Dieser User ist deaktiviert.",
            "user": None,
        }

    if not verify_password(password, user["password_hash"]):
        return {
            "success": False,
            "error_code": "INVALID_PASSWORD",
            "message": "Das Passwort ist nicht korrekt.",
            "user": None,
        }

    update_last_login(user["email"])

    return {
        "success": True,
        "error_code": None,
        "message": "Login erfolgreich.",
        "user": _session_user_from_user(user),
    }


def create_invited_user(
    email: str,
    display_name: str,
    role: str,
    invited_by: str,
    notes: str,
) -> dict:
    normalized_email = email.strip().lower()
    normalized_role = role.strip().lower()
    today = _today_string()

    existing_user = find_user_by_email(normalized_email)

    if existing_user:
        if existing_user["status"] == STATUS_DISABLED:
            return {
                "success": False,
                "error_code": "EMAIL_ALREADY_DISABLED",
                "message": f"Es gibt bereits einen deaktivierten User mit dieser Email-Adresse. Bitte aktiviere zuerst den Account.",
            }

        return {
            "success": False,
            "error_code": "EMAIL_ALREADY_EXISTS",
            "message": f"Es gibt bereits einen User mit der Email-Adresse {email}.",
        }

    if normalized_role not in ALLOWED_INVITE_ROLES:
        return {
            "success": False,
            "error_code": "INVALID_ROLE",
            "message": f"Die Rolle {role} ist nicht erlaubt.",
        }

    if not invited_by.strip():
        return {
            "success": False,
            "error_code": "MISSING_INVITED_BY",
            "message": "Bitte gib an, wer den User eingeladen hat.",
        }

    user_id = str(uuid4())
    temporary_password = generate_temporary_password()

    user = {
        "user_id": user_id,
        "email": normalized_email,
        "display_name": display_name.strip(),
        "role": normalized_role,
        "status": STATUS_INVITED,
        "password_hash": hash_password(temporary_password),
        "must_change_password": "TRUE",
        "created_at": today,
        "last_login_at": "",
        "invited_at": today,
        "invited_by": invited_by.strip(),
        "last_invite_sent_at": today,
        "disabled_at": "",
        "disabled_by": "",
        "notes": notes.strip(),
        "interests": "",
        "longterm": "",
        "midterm": "",
        "shortterm": "",
    }

    row = [
        user["user_id"],
        user["email"],
        user["display_name"],
        user["role"],
        user["status"],
        user["password_hash"],
        user["must_change_password"],
        user["created_at"],
        user["last_login_at"],
        user["invited_at"],
        user["invited_by"],
        user["last_invite_sent_at"],
        user["disabled_at"],
        user["disabled_by"],
        user["notes"],
        user["interests"],
        user["longterm"],
        user["midterm"],
        user["shortterm"],
    ]

    sheet = get_worksheet(USERS_WORKSHEET_NAME)
    sheet.append_row(row)

    clear_users_cache()

    email_result = None

    try:
        email_result = send_invite_email(
            to_email=normalized_email,
            display_name=display_name.strip(),
            temporary_password=temporary_password,
        )
    except Exception as exc:
        email_result = {
            "success": False,
            "message": str(exc),
        }

    return {
        "success": True,
        "error_code": None,
        "message": f"User {email} wurde erfolgreich eingeladen.",
        "temporary_password": temporary_password,
        "email": email_result,
        "user": _session_user_from_user(user),
    }

def resend_invite(email: str, invited_by: str) -> dict:
    user = find_user_by_email(email)

    if user is None:
        return {
            "success": False,
            "error_code": "USER_NOT_FOUND",
            "message": "User wurde nicht gefunden.",
            "temporary_password": None,
            "email": None,
            "user": None,
        }

    if user["status"] == STATUS_DISABLED:
        return {
            "success": False,
            "error_code": "USER_DISABLED",
            "message": "Deaktivierte User können keine neue Einladung erhalten.",
            "temporary_password": None,
            "email": None,
            "user": None,
        }

    if user["role"] == ROLE_ADMIN:
        return {
            "success": False,
            "error_code": "ADMIN_INVITE_NOT_ALLOWED",
            "message": "Für Admin-User kann über diese Funktion keine Einladung neu generiert werden.",
            "temporary_password": None,
            "email": None,
            "user": None,
        }

    if not invited_by.strip():
        return {
            "success": False,
            "error_code": "MISSING_INVITED_BY",
            "message": "Bitte gib an, wer die Einladung neu generiert hat.",
            "temporary_password": None,
            "email": None,
            "user": None,
        }

    row_index = _get_user_row_index_by_email(email)

    if row_index is None:
        return {
            "success": False,
            "error_code": "USER_ROW_NOT_FOUND",
            "message": "User-Zeile wurde nicht gefunden.",
            "temporary_password": None,
            "email": None,
            "user": None,
        }

    temporary_password = generate_temporary_password()
    today = _today_string()

    sheet = get_worksheet(USERS_WORKSHEET_NAME)
    sheet.update_cell(row_index, 5, STATUS_INVITED)
    sheet.update_cell(row_index, 6, hash_password(temporary_password))
    sheet.update_cell(row_index, 7, "TRUE")
    sheet.update_cell(row_index, 10, today)
    sheet.update_cell(row_index, 11, invited_by.strip())
    sheet.update_cell(row_index, 12, today)

    clear_users_cache()

    updated_user = find_user_by_email(email)
    email_result = None

    try:
        email_result = send_invite_email(
            to_email=updated_user["email"],
            display_name=updated_user["display_name"],
            temporary_password=temporary_password,
        )
    except Exception as exc:
        email_result = {
            "success": False,
            "message": str(exc),
        }

    return {
        "success": True,
        "error_code": None,
        "message": "Einladung wurde neu generiert.",
        "temporary_password": temporary_password,
        "email": email_result,
        "user": _session_user_from_user(updated_user),
    }


def disable_user(email: str, disabled_by: str) -> dict:
    user = find_user_by_email(email)

    if user is None:
        return {
            "success": False,
            "error_code": "USER_NOT_FOUND",
            "message": "User wurde nicht gefunden.",
        }

    if user["role"] == ROLE_ADMIN:
        return {
            "success": False,
            "error_code": "ADMIN_DISABLE_NOT_ALLOWED",
            "message": "Admin-User können über diese Funktion nicht deaktiviert werden.",
        }

    if user["email"] == disabled_by.strip().lower():
        return {
            "success": False,
            "error_code": "SELF_DISABLE_NOT_ALLOWED",
            "message": "Du kannst deinen eigenen Benutzer nicht deaktivieren.",
        }

    row_index = _get_user_row_index_by_email(email)

    if row_index is None:
        return {
            "success": False,
            "error_code": "USER_ROW_NOT_FOUND",
            "message": "User-Zeile wurde nicht gefunden.",
        }

    sheet = get_worksheet(USERS_WORKSHEET_NAME)
    sheet.update_cell(row_index, 5, STATUS_DISABLED)
    sheet.update_cell(row_index, 13, _today_string())
    sheet.update_cell(row_index, 14, disabled_by.strip())

    clear_users_cache()

    return {
        "success": True,
        "error_code": None,
        "message": "User wurde deaktiviert.",
    }

def reset_user_password(email: str) -> dict:
    user = find_user_by_email(email)

    if user is None:
        return {
            "success": False,
            "error_code": "USER_NOT_FOUND",
            "message": "User wurde nicht gefunden.",
        }

    if user["status"] == STATUS_DISABLED:
        return {
            "success": False,
            "error_code": "USER_DISABLED",
            "message": "Dieser User ist deaktiviert.",
        }

    row_index = _get_user_row_index_by_email(email)

    if row_index is None:
        return {
            "success": False,
            "error_code": "USER_ROW_NOT_FOUND",
            "message": "User-Zeile wurde nicht gefunden.",
        }

    temporary_password = generate_temporary_password()
    today = _today_string()

    sheet = get_worksheet(USERS_WORKSHEET_NAME)
    sheet.update_cell(row_index, 5, STATUS_ACTIVE)
    sheet.update_cell(row_index, 6, hash_password(temporary_password))
    sheet.update_cell(row_index, 7, "TRUE")
    sheet.update_cell(row_index, 12, today)

    clear_users_cache()

    try:
        email_result = send_invite_email(
            to_email=user["email"],
            display_name=user["display_name"],
            temporary_password=temporary_password,
        )
    except Exception as exc:
        email_result = {
            "success": False,
            "message": str(exc),
        }

    return {
        "success": True,
        "error_code": None,
        "message": "Ein temporäres Passwort wurde erstellt und per E-Mail verschickt.",
        "temporary_password": temporary_password,
        "email": email_result,
    }