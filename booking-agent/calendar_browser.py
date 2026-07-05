from datetime import date, datetime

from bookings import list_bookings

DATE_FORMAT = "%d.%m.%Y"


def _parse_booking_date(value: str) -> date:
    value = str(value).strip()

    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        return date.fromisoformat(value)


def _booking_to_calendar_event(booking: dict) -> dict:
    start_date = _parse_booking_date(booking["start_date"])
    end_date = _parse_booking_date(booking["end_date"])

    title = f"{booking['guest_name']} · {booking['guests']} Gäste"

    return {
        "id": booking["booking_id"],
        "title": title,
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "allDay": True,
        "backgroundColor": "#2563eb",
        "borderColor": "#1d4ed8",
        "textColor": "#ffffff",
        "classNames": ["booking-event-confirmed"],
        "extendedProps": {
            "booking_id": booking["booking_id"],
            "status": booking["status"],
            "guest_name": booking["guest_name"],
            "guest_email": booking["guest_email"],
            "guests": booking["guests"],
            "notes": booking["notes"],
            "start_date": booking["start_date"],
            "end_date": booking["end_date"],
            "created_by": booking["created_by"],
            "created_at": booking["created_at"],
        },
    }


def get_booking_calendar_events(include_cancelled: bool = False) -> list[dict]:
    bookings = list_bookings(include_cancelled=include_cancelled)
    events = []

    for booking in bookings:
        event = _booking_to_calendar_event(booking)

        if booking["status"] == "cancelled":
            event["title"] = f"✕ Storniert · {booking['guest_name']}"
            event["backgroundColor"] = "#e5e7eb"
            event["borderColor"] = "#9ca3af"
            event["textColor"] = "#6b7280"
            event["classNames"] = ["booking-event-cancelled"]

        events.append(event)

    return events


def get_calendar_options(initial_view: str = "dayGridMonth") -> dict:
    return {
        "initialView": initial_view,
        "locale": "de",
        "firstDay": 1,
        "height": 560,
        "contentHeight": 520,
        "aspectRatio": 1.65,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listMonth",
        },
        "buttonText": {
            "today": "Heute",
            "month": "Monat",
            "week": "Woche",
            "list": "Liste",
        },
        "weekends": True,
        "navLinks": True,
        "selectable": False,
        "editable": False,
        "eventDisplay": "block",
        "displayEventTime": False,
        "dayMaxEvents": 3,
        "moreLinkText": "mehr",
        "eventMinHeight": 18,
        "eventShortHeight": 18,
        "eventOrder": "title",
    }