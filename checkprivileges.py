from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "/Users/papi71/PycharmProjects/book_scareglia/bookscareglia-ce6215cc4f22.json"   # Pfad anpassen

SCOPES = [
    "https://www.googleapis.com/auth/gmail.settings.basic",
]

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES,
).with_subject("pascal@lmjp.ch")

service = build("gmail", "v1", credentials=creds)

aliases = service.users().settings().sendAs().list(
    userId="me"
).execute()

from pprint import pprint
pprint(aliases)