import json

import google.auth
import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_SERVICE_ACCOUNT_FILE, GOOGLE_SHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_gspread_client():
    if GOOGLE_SERVICE_ACCOUNT_FILE:
        credentials = Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
        )
    else:
        credentials, _ = google.auth.default(scopes=SCOPES)

    return gspread.authorize(credentials)


def get_spreadsheet():
    client = get_gspread_client()
    return client.open_by_key(GOOGLE_SHEET_ID)


def get_worksheet(name: str):
    spreadsheet = get_spreadsheet()
    return spreadsheet.worksheet(name)


def test_connection() -> dict:
    spreadsheet = get_spreadsheet()
    worksheets = spreadsheet.worksheets()

    return {
        "spreadsheet_title": spreadsheet.title,
        "worksheets": [worksheet.title for worksheet in worksheets],
    }