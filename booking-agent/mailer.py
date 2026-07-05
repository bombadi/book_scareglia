import base64
from email.message import EmailMessage

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import (
    APP_BASE_URL,
    GMAIL_SENDER_EMAIL,
    GOOGLE_SERVICE_ACCOUNT_FILE,
)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
]


def get_gmail_service():
    if not GMAIL_SENDER_EMAIL:
        raise RuntimeError("Missing required environment variable: GMAIL_SENDER_EMAIL")

    credentials = Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=GMAIL_SCOPES,
    )

    delegated_credentials = credentials.with_subject(GMAIL_SENDER_EMAIL)

    return build("gmail", "v1", credentials=delegated_credentials)


def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
) -> dict:
    message = EmailMessage()

    message["To"] = to_email
    message["From"] = GMAIL_SENDER_EMAIL
    message["Subject"] = subject

    if body_html:
        message.set_content(body_text)
        message.add_alternative(body_html, subtype="html")
    else:
        message.set_content(body_text)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    service = get_gmail_service()

    result = service.users().messages().send(
        userId="me",
        body={
            "raw": encoded_message,
        },
    ).execute()

    return {
        "success": True,
        "message_id": result.get("id"),
        "thread_id": result.get("threadId"),
    }

def send_html_report_email(
    to_email: str,
    subject: str,
    html_report: str,
) -> dict:
    body_text = (
        "Hallo,\n\n"
        "dein persönlicher Region-Report wurde erstellt. "
        "Bitte öffne diese E-Mail in einem HTML-fähigen E-Mail-Client.\n\n"
        "Freundliche Grüße\n"
        "Ferienhaus Agent"
    )

    return send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=html_report,
    )

def send_invite_email(
    to_email: str,
    display_name: str,
    temporary_password: str,
) -> dict:
    login_url = APP_BASE_URL

    subject = "Einladung zum Ferienhaus Buchungsagenten"

    body_text = f"""Hallo {display_name},

du wurdest zum Ferienhaus Buchungsagenten eingeladen.

Login:
{login_url}

E-Mail:
{to_email}

Temporäres Passwort:
{temporary_password}

Bitte ändere dein Passwort nach dem ersten Login.

Freundliche Grüße
Ferienhaus Buchungsagent
"""

    body_html = f"""
    <p>Hallo {display_name},</p>

    <p>du wurdest zum <strong>Ferienhaus Buchungsagenten</strong> eingeladen.</p>

    <p>
      <strong>Login:</strong><br>
      <a href="{login_url}">{login_url}</a>
    </p>

    <p>
      <strong>E-Mail:</strong><br>
      {to_email}
    </p>

    <p>
      <strong>Temporäres Passwort:</strong><br>
      <code>{temporary_password}</code>
    </p>

    <p>Bitte ändere dein Passwort nach dem ersten Login.</p>

    <p>Freundliche Grüße<br>Ferienhaus Buchungsagent</p>
    """

    return send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
    )

def send_booking_confirmation_email(booking: dict) -> dict:
    subject = f"Buchungsbestätigung {booking['booking_id']}"

    body_text = f"""Hallo {booking['guest_name']},

deine Buchung wurde erfolgreich erstellt.

Buchungsdetails:

Buchungs-ID:
{booking['booking_id']}

Anreise:
{booking['start_date']}

Abreise:
{booking['end_date']}

Gäste:
{booking['guests']}

Status:
{booking['status']}

Notizen:
{booking.get('notes', '') or '-'}

Du kannst deine Buchungen im Ferienhaus Agent unter "Meine Buchungen" einsehen.

Freundliche Grüße
Ferienhaus Agent
"""

    body_html = f"""
    <p>Hallo {booking['guest_name']},</p>

    <p>deine Buchung wurde erfolgreich erstellt.</p>

    <h3>Buchungsdetails</h3>

    <table>
      <tr>
        <td><strong>Buchungs-ID:</strong></td>
        <td>{booking['booking_id']}</td>
      </tr>
      <tr>
        <td><strong>Anreise:</strong></td>
        <td>{booking['start_date']}</td>
      </tr>
      <tr>
        <td><strong>Abreise:</strong></td>
        <td>{booking['end_date']}</td>
      </tr>
      <tr>
        <td><strong>Gäste:</strong></td>
        <td>{booking['guests']}</td>
      </tr>
      <tr>
        <td><strong>Status:</strong></td>
        <td>{booking['status']}</td>
      </tr>
      <tr>
        <td><strong>Notizen:</strong></td>
        <td>{booking.get('notes', '') or '-'}</td>
      </tr>
    </table>

    <p>Du kannst deine Buchungen im Ferienhaus Agent unter <strong>Meine Buchungen</strong> einsehen.</p>

    <p>Freundliche Grüße<br>Ferienhaus Agent</p>
    """

    return send_email(
        to_email=booking["guest_email"],
        subject=subject,
        body_text=body_text,
        body_html=body_html,
    )

def send_booking_update_email(booking: dict) -> dict:
    subject = f"Buchungsänderung {booking['booking_id']}"

    body_text = f"""Hallo {booking['guest_name']},

deine Buchung wurde aktualisiert.

Aktuelle Buchungsdetails:

Buchungs-ID:
{booking['booking_id']}

Anreise:
{booking['start_date']}

Abreise:
{booking['end_date']}

Gäste:
{booking['guests']}

Status:
{booking['status']}

Notizen:
{booking.get('notes', '') or '-'}

Du kannst deine Buchungen im Ferienhaus Agent unter "Meine Buchungen" einsehen.

Freundliche Grüße
Ferienhaus Agent
"""

    body_html = f"""
    <p>Hallo {booking['guest_name']},</p>

    <p>deine Buchung wurde aktualisiert.</p>

    <h3>Aktuelle Buchungsdetails</h3>

    <table>
      <tr>
        <td><strong>Buchungs-ID:</strong></td>
        <td>{booking['booking_id']}</td>
      </tr>
      <tr>
        <td><strong>Anreise:</strong></td>
        <td>{booking['start_date']}</td>
      </tr>
      <tr>
        <td><strong>Abreise:</strong></td>
        <td>{booking['end_date']}</td>
      </tr>
      <tr>
        <td><strong>Gäste:</strong></td>
        <td>{booking['guests']}</td>
      </tr>
      <tr>
        <td><strong>Status:</strong></td>
        <td>{booking['status']}</td>
      </tr>
      <tr>
        <td><strong>Notizen:</strong></td>
        <td>{booking.get('notes', '') or '-'}</td>
      </tr>
    </table>

    <p>Du kannst deine Buchungen im Ferienhaus Agent unter <strong>Meine Buchungen</strong> einsehen.</p>

    <p>Freundliche Grüße<br>Ferienhaus Agent</p>
    """

    return send_email(
        to_email=booking["guest_email"],
        subject=subject,
        body_text=body_text,
        body_html=body_html,
    )


def send_booking_cancellation_email(booking: dict) -> dict:
    subject = f"Buchung storniert {booking['booking_id']}"

    body_text = f"""Hallo {booking['guest_name']},

deine Buchung wurde storniert.

Buchungsdetails:

Buchungs-ID:
{booking['booking_id']}

Anreise:
{booking['start_date']}

Abreise:
{booking['end_date']}

Gäste:
{booking['guests']}

Status:
{booking['status']}

Freundliche Grüße
Ferienhaus Agent
"""

    body_html = f"""
    <p>Hallo {booking['guest_name']},</p>

    <p>deine Buchung wurde storniert.</p>

    <h3>Buchungsdetails</h3>

    <table>
      <tr>
        <td><strong>Buchungs-ID:</strong></td>
        <td>{booking['booking_id']}</td>
      </tr>
      <tr>
        <td><strong>Anreise:</strong></td>
        <td>{booking['start_date']}</td>
      </tr>
      <tr>
        <td><strong>Abreise:</strong></td>
        <td>{booking['end_date']}</td>
      </tr>
      <tr>
        <td><strong>Gäste:</strong></td>
        <td>{booking['guests']}</td>
      </tr>
      <tr>
        <td><strong>Status:</strong></td>
        <td>{booking['status']}</td>
      </tr>
    </table>

    <p>Freundliche Grüße<br>Ferienhaus Agent</p>
    """

    return send_email(
        to_email=booking["guest_email"],
        subject=subject,
        body_text=body_text,
        body_html=body_html,
    )