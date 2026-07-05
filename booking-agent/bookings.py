from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from google_sheets import get_worksheet

BOOKINGS_WORKSHEET_NAME = "bookings"

STATUS_CONFIRMED = "confirmed"
STATUS_CANCELLED = "cancelled"

DATE_FORMAT = "%d.%m.%Y"
CANCELLATION_DAYS_BEFORE_ARRIVAL = 7
SHORT_NOTICE_CANCELLATION_DAYS = 7


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _today() -> date:
    return _now().date()


def _now_date_string() -> str:
    return _format_date(_today())


def _format_date(value: date) -> str:
    return value.strftime(DATE_FORMAT)


def _parse_date(value: str) -> date:
    value = str(value).strip()

    if not value:
        raise ValueError("Date value is empty.")

    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        return date.fromisoformat(value)


def _parse_datetime(value: str) -> datetime:
    value = str(value).strip()

    if not value:
        raise ValueError("Datetime value is empty.")

    try:
        parsed_date = datetime.strptime(value, DATE_FORMAT).date()
        return datetime.combine(parsed_date, datetime.min.time(), tzinfo=timezone.utc)
    except ValueError:
        parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _normalize_row(row: dict) -> dict:
    return {
        "booking_id": str(row.get("booking_id", "")).strip(),
        "status": str(row.get("status", "")).strip(),
        "guest_name": str(row.get("guest_name", "")).strip(),
        "guest_email": str(row.get("guest_email", "")).strip(),
        "start_date": str(row.get("start_date", "")).strip(),
        "end_date": str(row.get("end_date", "")).strip(),
        "guests": int(row.get("guests") or 0),
        "notes": str(row.get("notes", "")).strip(),
        "created_by": str(row.get("created_by", "")).strip(),
        "created_at": str(row.get("created_at", "")).strip(),
        "cancelled_by": str(row.get("cancelled_by", "")).strip(),
        "cancelled_at": str(row.get("cancelled_at", "")).strip(),
    }


def _get_bookings_sheet():
    return get_worksheet(BOOKINGS_WORKSHEET_NAME)


def list_bookings(include_cancelled: bool = False) -> list[dict]:
    sheet = _get_bookings_sheet()
    rows = sheet.get_all_records()

    bookings = [_normalize_row(row) for row in rows]

    if include_cancelled:
        return bookings

    return [
        booking
        for booking in bookings
        if booking["status"] == STATUS_CONFIRMED
    ]

def filter_bookings(
    include_cancelled: bool = False,
    start_date: date | None = None,
    end_date: date | None = None,
    user_email: str = "",
) -> list[dict]:
    bookings = list_bookings(include_cancelled=include_cancelled)
    normalized_email = user_email.strip().lower()

    filtered_bookings = []

    for booking in bookings:
        if normalized_email:
            guest_email = booking["guest_email"].strip().lower()
            created_by = booking["created_by"].strip().lower()

            if guest_email != normalized_email and created_by != normalized_email:
                continue

        if start_date is not None or end_date is not None:
            booking_start = _parse_date(booking["start_date"])
            booking_end = _parse_date(booking["end_date"])

            filter_start = start_date or date.min
            filter_end = end_date or date.max

            if not dates_overlap(
                requested_start=filter_start,
                requested_end=filter_end,
                existing_start=booking_start,
                existing_end=booking_end,
            ):
                continue

        filtered_bookings.append(booking)

    return filtered_bookings

def dates_overlap(
    requested_start: date,
    requested_end: date,
    existing_start: date,
    existing_end: date,
) -> bool:
    return requested_start < existing_end and existing_start < requested_end


def check_availability(
    start_date: date,
    end_date: date,
    ignore_booking_id: str | None = None,
    mode: str = "full_period",
) -> dict:
    today = _today()

    if start_date >= end_date:
        return {
            "available": False,
            "error_code": "INVALID_DATE_RANGE",
            "message": "Das Anreisedatum muss vor dem Abreisedatum liegen.",
            "conflicts": [],
            "periods": [],
        }

    if mode == "available_periods":
        effective_start_date = max(start_date, today)

        if effective_start_date >= end_date:
            return {
                "available": False,
                "error_code": "NO_FUTURE_DAYS_IN_RANGE",
                "message": "Für diesen Zeitraum gibt es keine zukünftigen Tage mehr.",
                "conflicts": [],
                "periods": [],
            }

        confirmed_bookings = list_bookings(include_cancelled=False)
        overlapping_bookings = []

        for booking in confirmed_bookings:
            existing_start = _parse_date(booking["start_date"])
            existing_end = _parse_date(booking["end_date"])

            if dates_overlap(
                requested_start=effective_start_date,
                requested_end=end_date,
                existing_start=existing_start,
                existing_end=existing_end,
            ):
                overlapping_bookings.append(
                    {
                        **booking,
                        "_parsed_start_date": existing_start,
                        "_parsed_end_date": existing_end,
                    }
                )

        overlapping_bookings.sort(key=lambda booking: booking["_parsed_start_date"])

        periods = []
        cursor = effective_start_date

        for booking in overlapping_bookings:
            booked_start = max(booking["_parsed_start_date"], effective_start_date)
            booked_end = min(booking["_parsed_end_date"], end_date)

            if cursor < booked_start:
                periods.append(
                    {
                        "start_date": _format_date(cursor),
                        "end_date": _format_date(booked_start),
                    }
                )

            if cursor < booked_end:
                cursor = booked_end

        if cursor < end_date:
            periods.append(
                {
                    "start_date": _format_date(cursor),
                    "end_date": _format_date(end_date),
                }
            )

        return {
            "available": len(periods) > 0,
            "error_code": None if periods else "NO_AVAILABLE_PERIODS",
            "message": (
                "Es gibt noch freie Zeiträume."
                if periods
                else "Für diesen Zeitraum ist leider nichts mehr frei."
            ),
            "conflicts": [],
            "periods": periods,
        }

    if start_date < today:
        return {
            "available": False,
            "error_code": "START_DATE_IN_PAST",
            "message": "Das Anreisedatum darf nicht in der Vergangenheit liegen.",
            "conflicts": [],
            "periods": [],
        }

    confirmed_bookings = list_bookings(include_cancelled=False)
    conflicts = []
    ignored_booking_id = (ignore_booking_id or "").strip()

    for booking in confirmed_bookings:
        if ignored_booking_id and booking["booking_id"] == ignored_booking_id:
            continue

        existing_start = _parse_date(booking["start_date"])
        existing_end = _parse_date(booking["end_date"])

        if dates_overlap(start_date, end_date, existing_start, existing_end):
            conflicts.append(booking)

    if conflicts:
        return {
            "available": False,
            "error_code": "NOT_AVAILABLE",
            "message": "Der gewünschte Zeitraum ist leider bereits belegt.",
            "conflicts": conflicts,
            "periods": [],
        }

    return {
        "available": True,
        "error_code": None,
        "message": "Der gewünschte Zeitraum ist verfügbar.",
        "conflicts": [],
        "periods": [
            {
                "start_date": _format_date(start_date),
                "end_date": _format_date(end_date),
            }
        ],
    }


def create_booking(
    guest_name: str,
    guest_email: str,
    start_date: date,
    end_date: date,
    guests: int,
    notes: str = "",
    created_by: str = "",
) -> dict:
    if not guest_name.strip():
        return {
            "success": False,
            "error_code": "MISSING_GUEST_NAME",
            "message": "Der Name des Gasts fehlt.",
        }

    if not guest_email.strip():
        return {
            "success": False,
            "error_code": "MISSING_GUEST_EMAIL",
            "message": "Die E-Mail-Adresse des Gasts fehlt.",
        }

    if guests < 1:
        return {
            "success": False,
            "error_code": "INVALID_GUEST_COUNT",
            "message": "Die Anzahl der Gäste muss mindestens 1 sein.",
        }

    availability = check_availability(start_date, end_date)

    if not availability["available"]:
        return {
            "success": False,
            "error_code": availability["error_code"],
            "message": availability["message"],
            "conflicts": availability["conflicts"],
        }

    booking_id = f"BK-{uuid4().hex[:8].upper()}"

    booking = {
        "booking_id": booking_id,
        "status": STATUS_CONFIRMED,
        "guest_name": guest_name.strip(),
        "guest_email": guest_email.strip(),
        "start_date": _format_date(start_date),
        "end_date": _format_date(end_date),
        "guests": guests,
        "notes": notes.strip(),
        "created_by": created_by.strip(),
        "created_at": _now_date_string(),
        "cancelled_by": "",
        "cancelled_at": "",
    }

    row = [
        booking["booking_id"],
        booking["status"],
        booking["guest_name"],
        booking["guest_email"],
        booking["start_date"],
        booking["end_date"],
        booking["guests"],
        booking["notes"],
        booking["created_by"],
        booking["created_at"],
        booking["cancelled_by"],
        booking["cancelled_at"],
    ]

    sheet = _get_bookings_sheet()
    sheet.append_row(row, value_input_option="USER_ENTERED")

    return {
        "success": True,
        "message": "Die Buchung wurde erstellt.",
        "booking": booking,
    }


def find_booking_by_id(booking_id: str) -> dict | None:
    bookings = list_bookings(include_cancelled=True)

    for booking in bookings:
        if booking["booking_id"] == booking_id.strip():
            return booking

    return None


def update_booking(
    booking_id: str,
    guest_name: str,
    guest_email: str,
    start_date: date,
    end_date: date,
    guests: int,
    notes: str = "",
) -> dict:
    booking_id = booking_id.strip()
    booking = find_booking_by_id(booking_id)

    if booking is None:
        return {
            "success": False,
            "error_code": "BOOKING_NOT_FOUND",
            "message": "Die Buchung wurde nicht gefunden.",
            "booking": None,
        }

    if booking["status"] == STATUS_CANCELLED:
        return {
            "success": False,
            "error_code": "BOOKING_CANCELLED",
            "message": "Stornierte Buchungen können nicht bearbeitet werden.",
            "booking": booking,
        }

    original_start_date = _parse_date(booking["start_date"])

    if _today() >= original_start_date:
        return {
            "success": False,
            "error_code": "STAY_ALREADY_STARTED",
            "message": "Diese Buchung kann nicht mehr bearbeitet werden, da der Aufenthalt bereits begonnen hat oder vorbei ist.",
            "booking": booking,
        }

    if not guest_name.strip():
        return {
            "success": False,
            "error_code": "MISSING_GUEST_NAME",
            "message": "Der Name des Gasts fehlt.",
            "booking": booking,
        }

    if not guest_email.strip():
        return {
            "success": False,
            "error_code": "MISSING_GUEST_EMAIL",
            "message": "Die E-Mail-Adresse des Gasts fehlt.",
            "booking": booking,
        }

    if guests < 1:
        return {
            "success": False,
            "error_code": "INVALID_GUEST_COUNT",
            "message": "Die Anzahl der Gäste muss mindestens 1 sein.",
            "booking": booking,
        }

    availability = check_availability(
        start_date=start_date,
        end_date=end_date,
        ignore_booking_id=booking_id,
    )

    if not availability["available"]:
        return {
            "success": False,
            "error_code": availability["error_code"],
            "message": availability["message"],
            "conflicts": availability["conflicts"],
            "booking": booking,
        }

    sheet = _get_bookings_sheet()
    rows = sheet.get_all_records()

    updated_booking = {
        **booking,
        "guest_name": guest_name.strip(),
        "guest_email": guest_email.strip(),
        "start_date": _format_date(start_date),
        "end_date": _format_date(end_date),
        "guests": guests,
        "notes": notes.strip(),
    }

    for index, row in enumerate(rows, start=2):
        current_booking_id = str(row.get("booking_id", "")).strip()

        if current_booking_id != booking_id:
            continue

        sheet.update_cell(index, 3, updated_booking["guest_name"])
        sheet.update_cell(index, 4, updated_booking["guest_email"])
        sheet.update_cell(index, 5, updated_booking["start_date"])
        sheet.update_cell(index, 6, updated_booking["end_date"])
        sheet.update_cell(index, 7, updated_booking["guests"])
        sheet.update_cell(index, 8, updated_booking["notes"])

        return {
            "success": True,
            "error_code": None,
            "message": "Die Buchung wurde aktualisiert.",
            "booking": updated_booking,
        }

    return {
        "success": False,
        "error_code": "BOOKING_ROW_NOT_FOUND",
        "message": "Buchungszeile wurde nicht gefunden.",
        "booking": booking,
    }


def can_cancel_booking(booking: dict) -> dict:
    today = _today()
    now = _now()

    start_date = _parse_date(booking["start_date"])
    end_date = _parse_date(booking["end_date"])
    created_at = _parse_datetime(booking["created_at"])

    if today >= start_date:
        return {
            "allowed": False,
            "error_code": "STAY_ALREADY_STARTED",
            "message": "Diese Buchung kann nicht mehr storniert werden, da der Aufenthalt bereits begonnen hat oder vorbei ist.",
        }

    if today >= end_date:
        return {
            "allowed": False,
            "error_code": "STAY_ALREADY_ENDED",
            "message": "Diese Buchung kann nicht mehr storniert werden, da der Aufenthalt bereits vorbei ist.",
        }

    regular_cancellation_deadline = start_date - timedelta(
        days=CANCELLATION_DAYS_BEFORE_ARRIVAL,
    )

    if today <= regular_cancellation_deadline:
        return {
            "allowed": True,
            "error_code": None,
            "message": "Die Buchung kann regulär storniert werden.",
        }

    was_booked_within_7_days_before_arrival = created_at.date() > regular_cancellation_deadline
    short_notice_cancellation_deadline = created_at + timedelta(
        days=SHORT_NOTICE_CANCELLATION_DAYS,
    )

    if was_booked_within_7_days_before_arrival and now <= short_notice_cancellation_deadline:
        return {
            "allowed": True,
            "error_code": None,
            "message": "Die Buchung kann innerhalb der 7-Tage-Frist ab Buchungszeitpunkt storniert werden.",
        }

    return {
        "allowed": False,
        "error_code": "CANCELLATION_DEADLINE_EXPIRED",
        "message": "Die Stornierungsfrist ist abgelaufen. Eine Stornierung ist nur bis spätestens 7 Tage vor Anreise möglich. Kurzfristige Buchungen können innerhalb von 7 Tagen ab Buchungszeitpunkt storniert werden.",
    }


def get_cancellation_status(booking_id: str) -> dict:
    booking_id = booking_id.strip()

    if not booking_id:
        return {
            "success": False,
            "allowed": False,
            "error_code": "MISSING_BOOKING_ID",
            "message": "Die Buchungs-ID fehlt.",
            "booking": None,
        }

    booking = find_booking_by_id(booking_id)

    if booking is None:
        return {
            "success": False,
            "allowed": False,
            "error_code": "BOOKING_NOT_FOUND",
            "message": "Die Buchung wurde nicht gefunden.",
            "booking": None,
        }

    if booking["status"] == STATUS_CANCELLED:
        return {
            "success": True,
            "allowed": False,
            "error_code": "ALREADY_CANCELLED",
            "message": "Diese Buchung ist bereits storniert.",
            "booking": booking,
        }

    cancellation_check = can_cancel_booking(booking)

    return {
        "success": True,
        "allowed": cancellation_check["allowed"],
        "error_code": cancellation_check["error_code"],
        "message": cancellation_check["message"],
        "booking": booking,
    }


def list_bookings_for_user(
    user_email: str,
    include_cancelled: bool = True,
) -> list[dict]:
    normalized_email = user_email.strip().lower()
    bookings = list_bookings(include_cancelled=include_cancelled)

    return [
        booking
        for booking in bookings
        if booking["guest_email"].strip().lower() == normalized_email
        or booking["created_by"].strip().lower() == normalized_email
    ]


def get_cancellation_deadline(booking: dict) -> date | None:
    if booking["status"] == STATUS_CANCELLED:
        return None

    today = _today()
    now = _now()

    start_date = _parse_date(booking["start_date"])
    end_date = _parse_date(booking["end_date"])
    created_at = _parse_datetime(booking["created_at"])

    if today >= start_date or today >= end_date:
        return None

    regular_cancellation_deadline = start_date - timedelta(
        days=CANCELLATION_DAYS_BEFORE_ARRIVAL,
    )

    if today <= regular_cancellation_deadline:
        return regular_cancellation_deadline

    was_booked_within_7_days_before_arrival = created_at.date() > regular_cancellation_deadline
    short_notice_cancellation_deadline = created_at + timedelta(
        days=SHORT_NOTICE_CANCELLATION_DAYS,
    )

    if was_booked_within_7_days_before_arrival and now <= short_notice_cancellation_deadline:
        return short_notice_cancellation_deadline.date()

    return None


def get_cancellation_action(booking: dict) -> dict:
    cancellation_status = get_cancellation_status(booking["booking_id"])
    deadline = get_cancellation_deadline(booking)

    if not cancellation_status["success"]:
        return {
            "allowed": False,
            "label": "Stornieren",
            "message": cancellation_status["message"],
            "deadline": None,
            "days_left": None,
        }

    if not cancellation_status["allowed"] or deadline is None:
        return {
            "allowed": False,
            "label": "Stornieren",
            "message": cancellation_status["message"],
            "deadline": None,
            "days_left": None,
        }

    days_left = max((deadline - _today()).days, 0)

    if days_left == 0:
        label = "Stornieren (letzter Tag)"
    elif days_left == 1:
        label = "Stornieren (noch 1 Tag)"
    else:
        label = f"Stornieren (noch {days_left} Tage)"

    return {
        "allowed": True,
        "label": label,
        "message": cancellation_status["message"],
        "deadline": _format_date(deadline),
        "days_left": days_left,
    }


def cancel_booking(booking_id: str, cancelled_by: str = "") -> dict:
    booking_id = booking_id.strip()

    if not booking_id:
        return {
            "success": False,
            "error_code": "MISSING_BOOKING_ID",
            "message": "Die Buchungs-ID fehlt.",
        }

    cancellation_status = get_cancellation_status(booking_id)

    if not cancellation_status["success"]:
        return {
            "success": False,
            "error_code": cancellation_status["error_code"],
            "message": cancellation_status["message"],
        }

    if not cancellation_status["allowed"]:
        return {
            "success": False,
            "error_code": cancellation_status["error_code"],
            "message": cancellation_status["message"],
            "booking": cancellation_status["booking"],
        }

    sheet = _get_bookings_sheet()
    rows = sheet.get_all_records()

    for index, row in enumerate(rows, start=2):
        current_booking_id = str(row.get("booking_id", "")).strip()

        if current_booking_id != booking_id:
            continue

        sheet.update_cell(index, 2, STATUS_CANCELLED)
        sheet.update_cell(index, 11, cancelled_by.strip())
        sheet.update_cell(index, 12, _now_date_string())

        cancelled_booking = {
            **cancellation_status["booking"],
            "status": STATUS_CANCELLED,
            "cancelled_by": cancelled_by.strip(),
            "cancelled_at": _now_date_string(),
        }

        return {
            "success": True,
            "message": "Die Buchung wurde storniert.",
            "booking_id": booking_id,
            "booking": cancelled_booking,
        }

    return {
        "success": False,
        "error_code": "BOOKING_NOT_FOUND",
        "message": "Die Buchung wurde nicht gefunden.",
    }