from datetime import date, timedelta
from uuid import uuid4

from google_sheets import get_worksheet

BOOKINGS_WORKSHEET_NAME = "bookings"
DATE_FORMAT = "%d.%m.%Y"

STATUS_CONFIRMED = "confirmed"
STATUS_CANCELLED = "cancelled"

BOOKINGS_HEADER = [
    "booking_id",
    "status",
    "guest_name",
    "guest_email",
    "start_date",
    "end_date",
    "guests",
    "notes",
    "created_by",
    "created_at",
    "cancelled_by",
    "cancelled_at",
]


def _format_date(value: date) -> str:
    return value.strftime(DATE_FORMAT)


def _booking_id() -> str:
    return f"BK-{uuid4().hex[:8].upper()}"


def build_test_bookings(today: date | None = None) -> list[list]:
    if today is None:
        today = date.today()

    return [
        [
            _booking_id(),
            STATUS_CONFIRMED,
            "Test Gast Verfügbar",
            "test.available@example.com",
            _format_date(today + timedelta(days=14)),
            _format_date(today + timedelta(days=18)),
            2,
            "Reguläre zukünftige Buchung, stornierbar.",
            "seed",
            _format_date(today - timedelta(days=20)),
            "",
            "",
        ],
        [
            _booking_id(),
            STATUS_CONFIRMED,
            "Test Gast Bald",
            "test.soon@example.com",
            _format_date(today + timedelta(days=5)),
            _format_date(today + timedelta(days=8)),
            4,
            "Kurzfristige Buchung, innerhalb von 7 Tagen vor Anreise erstellt.",
            "seed",
            _format_date(today - timedelta(days=1)),
            "",
            "",
        ],
        [
            _booking_id(),
            STATUS_CONFIRMED,
            "Test Gast Frist Abgelaufen",
            "test.expired@example.com",
            _format_date(today + timedelta(days=5)),
            _format_date(today + timedelta(days=10)),
            3,
            "Nicht mehr regulär stornierbar, da weniger als 7 Tage vor Anreise und nicht kurzfristig erstellt.",
            "seed",
            _format_date(today - timedelta(days=20)),
            "",
            "",
        ],
        [
            _booking_id(),
            STATUS_CONFIRMED,
            "Test Gast Laufend",
            "test.active@example.com",
            _format_date(today - timedelta(days=1)),
            _format_date(today + timedelta(days=3)),
            2,
            "Aufenthalt läuft bereits, Storno nicht erlaubt.",
            "seed",
            _format_date(today - timedelta(days=10)),
            "",
            "",
        ],
        [
            _booking_id(),
            STATUS_CONFIRMED,
            "Test Gast Vergangen",
            "test.past@example.com",
            _format_date(today - timedelta(days=10)),
            _format_date(today - timedelta(days=5)),
            2,
            "Vergangener Aufenthalt, Storno nicht erlaubt.",
            "seed",
            _format_date(today - timedelta(days=30)),
            "",
            "",
        ],
        [
            _booking_id(),
            STATUS_CANCELLED,
            "Test Gast Storniert",
            "test.cancelled@example.com",
            _format_date(today + timedelta(days=25)),
            _format_date(today + timedelta(days=30)),
            2,
            "Bereits stornierte Testbuchung.",
            "seed",
            _format_date(today - timedelta(days=5)),
            "seed",
            _format_date(today - timedelta(days=3)),
        ],
    ]


def seed_bookings_sheet(clear_existing: bool = False) -> dict:
    sheet = get_worksheet(BOOKINGS_WORKSHEET_NAME)

    if clear_existing:
        sheet.clear()
        sheet.append_row(BOOKINGS_HEADER, value_input_option="USER_ENTERED")
    else:
        existing_values = sheet.get_all_values()

        if not existing_values:
            sheet.append_row(BOOKINGS_HEADER, value_input_option="USER_ENTERED")

    test_bookings = build_test_bookings()
    sheet.append_rows(test_bookings, value_input_option="USER_ENTERED")

    return {
        "success": True,
        "message": "Testdaten wurden eingefügt.",
        "inserted_rows": len(test_bookings),
        "cleared_existing": clear_existing,
    }


if __name__ == "__main__":
    result = seed_bookings_sheet(clear_existing=False)
    print(result)