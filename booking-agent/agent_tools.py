from datetime import date, datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

from bookings import check_availability, get_cancellation_status, create_booking, filter_bookings
from calendar_browser import get_booking_calendar_events
from travel_reports import create_region_report_html

TIMEZONE = "Europe/Zurich"
HOLIDAY_HOME_LOCATION = "Scareglia"

def build_sbb_search_url(
    from_name: str,
    from_id: str,
    to_name: str,
    to_id: str,
    travel_date: str,
    travel_time: str = "08:00",
    moment: str = "dep",
) -> str:
    time_value = travel_time.replace(":", "_")
    stops = f"{from_name}_I{from_id}~{to_name}_I{to_id}"

    return (
        "https://www.sbb.ch/de?"
        f"stops={quote(stops, safe='~')}"
        f"&day={travel_date}"
        f"&time={time_value}"
        f"&moment={moment}"
    )

def tool_open_sbb_timetable(
    from_name: str,
    from_id: str,
    to_name: str,
    to_id: str,
    travel_date: str,
    travel_time: str = "08:00",
    moment: str = "dep",
) -> dict:
    sbb_url = build_sbb_search_url(
        from_name=from_name,
        from_id=from_id,
        to_name=to_name,
        to_id=to_id,
        travel_date=travel_date,
        travel_time=travel_time,
        moment=moment,
    )

    return {
        "message": "Ich öffne den SBB-Fahrplan mit den bekannten Reisedaten.",
        "artifacts": [
            {
                "type": "external_link",
                "title": "SBB-Fahrplan öffnen",
                "url": sbb_url,
                "label": "🚆 SBB-Fahrplan öffnen",
            }
        ],
        "data": {
            "url": sbb_url,
        },
        "kind": "final_result",
        "continue_agent": False,
    }

def tool_list_bookings(
    include_cancelled: bool = False,
    start_date: str = "",
    end_date: str = "",
    only_current_user: bool = False,
    current_user: dict | None = None,
) -> dict:
    current_user = current_user or {}

    parsed_start_date = date.fromisoformat(start_date) if start_date else None
    parsed_end_date = date.fromisoformat(end_date) if end_date else None
    user_email = current_user.get("email", "") if only_current_user else ""

    bookings = filter_bookings(
        include_cancelled=include_cancelled,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        user_email=user_email,
    )

    return {
        "message": "Hier ist die gefilterte Buchungsübersicht.",
        "continue_agent": False,
        "kind": "final_result",
        "artifacts": [
            {
                "type": "booking_list",
                "title": "Buchungen",
                "data": bookings,
            }
        ],
    }

def tool_prepare_booking(
    guest_name: str,
    guest_email: str,
    start_date: str,
    end_date: str,
    guests: int,
    notes: str = "",
    current_user: dict | None = None,
) -> dict:
    current_user = current_user or {}

    resolved_guest_name = guest_name.strip() or current_user.get("name", "").strip()
    resolved_guest_email = guest_email.strip() or current_user.get("email", "").strip()

    return {
        "message": "Ich habe die Buchungsdaten vorbereitet. Bitte bestätige die Buchung im Dialog.",
        "artifacts": [
            {
                "type": "booking_confirmation_required",
                "title": "Buchung bestätigen",
                "data": {
                    "guest_name": resolved_guest_name,
                    "guest_email": resolved_guest_email,
                    "start_date": start_date,
                    "end_date": end_date,
                    "guests": int(guests),
                    "notes": notes.strip(),
                    "created_by": current_user.get("email", ""),
                },
            }
        ],
        "kind": "final_result",
        "continue_agent": False,
    }

def tool_create_booking(
    guest_name: str,
    guest_email: str,
    start_date: str,
    end_date: str,
    guests: int,
    notes: str = "",
    current_user: dict | None = None,
) -> dict:
    parsed_start_date = date.fromisoformat(start_date)
    parsed_end_date = date.fromisoformat(end_date)

    current_user = current_user or {}

    result = create_booking(
        guest_name=guest_name,
        guest_email=guest_email,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        guests=guests,
        notes=notes,
        created_by=current_user.get("email", ""),
    )

    return {
        "message": result["message"],
        "artifacts": [
            {
                "type": "booking_result",
                "title": "Buchung",
                "data": result,
            }
        ],
        "data": result,
        "kind": "final_result",
        "continue_agent": False,
    }

def tool_get_current_date() -> dict:
    now = datetime.now(ZoneInfo(TIMEZONE))

    iso_date = now.date().isoformat()
    ch_date = now.strftime("%d.%m.%Y")

    return {
        "message": f"Heutiges Datum ist {ch_date}.",
        "artifacts": [],
        "continue_agent": True,
        "kind": "context",
        "data": {
            "date_iso": iso_date,
            "date_ch": ch_date,
            "datetime": now.isoformat(),
            "timezone": TIMEZONE,
        },
    }

def add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1

    days_in_month = [
        31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]

    day = min(value.day, days_in_month[month - 1])

    return value.replace(year=year, month=month, day=day)

def tool_calculate_date_offset(amount: int, unit: str) -> dict:
    now = datetime.now(ZoneInfo(TIMEZONE))

    if unit == "days":
        target = now + timedelta(days=amount)
    elif unit == "weeks":
        target = now + timedelta(weeks=amount)
    elif unit == "months":
        target = add_months(now, amount)
    else:
        return {
            "message": "Die Zeiteinheit konnte nicht verarbeitet werden.",
            "artifacts": [],
            "data": {},
        }

    return {
        "message": f"Das entspricht dem {target.strftime('%d.%m.%Y')}.",
        "artifacts": [],
        "continue_agent": True,
        "kind": "context",
        "data": {
            "date_iso": target.date().isoformat(),
            "date_ch": target.strftime("%d.%m.%Y"),
            "datetime": target.isoformat(),
            "timezone": TIMEZONE,
        },
    }

def tool_show_calendar(include_cancelled: bool = False) -> dict:
    events = get_booking_calendar_events(include_cancelled=include_cancelled)

    return {
        "message": "Hier ist der Buchungskalender.",
        "continue_agent": False,
        "kind": "final_result",
        "artifacts": [
            {
                "type": "booking_calendar",
                "title": "Buchungskalender",
                "events": events,
                "key": "agent_booking_calendar",
            }
        ],
    }

def tool_check_availability(start_date: str, end_date: str, mode: str = "full_period") -> dict:
    parsed_start_date = date.fromisoformat(start_date)
    parsed_end_date = date.fromisoformat(end_date)

    result = check_availability(
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        mode=mode,
    )

    return {
        "message": result["message"],
        "continue_agent": True,
        "kind": "final_result",
        "artifacts": [
            {
                "type": "availability_result",
                "title": "Verfügbarkeit",
                "data": result,
            }
        ],
    }

def tool_get_cancellation_status(booking_id: str) -> dict:
    result = get_cancellation_status(booking_id)

    return {
        "message": result["message"],
        "continue_agent": False,
        "kind": "final_result",
        "artifacts": [
            {
                "type": "cancellation_status",
                "title": "Stornierbarkeit",
                "data": result,
            }
        ],
    }

def tool_create_region_report(
    region: str,
    start_date: str,
    end_date: str,
    current_user: dict,
    ) -> dict:
    report = create_region_report_html(
        region=region,
        start_date=start_date,
        end_date=end_date,
        interests=current_user.get("interests", ""),
        guest_name=current_user.get("name", ""),
    )

    return {
        "message": "Ich habe einen Region-Report für deinen Aufenthalt erstellt.",
        "continue_agent": False,
        "kind": "final_result",
        "artifacts": [
            {
                "type": "html_report",
                "title": report["title"],
                "html": report["html"],
                "email_subject": report["title"],
                "sources": report.get("sources", []),
                "reflection": report.get("reflection", {}),
                "initial_queries": report.get("initial_queries", []),
                "additional_queries": report.get("additional_queries", []),
            }
        ],
    }

TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "open_sbb_timetable",
        "description": "Erstellt einen SBB-Fahrplanlink für Anreise oder Rückreise und öffnet ihn über die UI.",
        "parameters": {
            "type": "object",
            "properties": {
                "from_name": {
                    "type": "string",
                    "description": "Startort, z. B. Basel"
                },
                "from_id": {
                    "type": "string",
                    "description": "SBB/Transport-ID des Startorts, z. B. 22"
                },
                "to_name": {
                    "type": "string",
                    "description": "Zielort, z. B. Scareglia"
                },
                "to_id": {
                    "type": "string",
                    "description": "SBB/Transport-ID des Zielorts"
                },
                "travel_date": {
                    "type": "string",
                    "description": "Reisedatum im ISO-Format YYYY-MM-DD"
                },
                "travel_time": {
                    "type": "string",
                    "description": "Uhrzeit im Format HH:MM"
                },
                "moment": {
                    "type": "string",
                    "enum": ["dep", "arr"],
                    "description": "dep = Abfahrt, arr = Ankunft"
                }
            },
            "required": ["from_name", "from_id", "to_name", "to_id", "travel_date"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "list_bookings",
        "description": "Zeigt eine Liste der Buchungen an. Kann nach Zeitraum und aktuellem User gefiltert werden.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_cancelled": {
                    "type": "boolean",
                    "description": "Ob stornierte Buchungen eingeschlossen werden sollen.",
                },
                "start_date": {
                    "type": "string",
                    "description": "Optionaler Start des Filterzeitraums im ISO-Format YYYY-MM-DD.",
                },
                "end_date": {
                    "type": "string",
                    "description": "Optionales Ende des Filterzeitraums im ISO-Format YYYY-MM-DD. Der Zeitraum ist exklusiv wie bei Abreisedaten.",
                },
                "only_current_user": {
                    "type": "boolean",
                    "description": "Wenn true, werden nur Buchungen angezeigt, bei denen der aktuelle User Gast oder Ersteller ist.",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "prepare_booking",
        "description": "Bereitet eine Buchung zur verbindlichen Bestätigung durch den User vor. Erstellt noch keine Buchung.",
        "parameters": {
            "type": "object",
            "properties": {
                "guest_name": {
                    "type": "string",
                    "description": "Name des Gasts. Optional, wenn der aktuelle User für sich selbst bucht."
                },
                "guest_email": {
                    "type": "string",
                    "description": "E-Mail-Adresse des Gasts. Optional, wenn der aktuelle User für sich selbst bucht."
                },
                "start_date": {
                    "type": "string",
                    "description": "Anreisedatum im ISO-Format YYYY-MM-DD"
                },
                "end_date": {
                    "type": "string",
                    "description": "Abreisedatum im ISO-Format YYYY-MM-DD"
                },
                "guests": {
                    "type": "integer",
                    "description": "Anzahl der Gäste"
                },
                "notes": {
                    "type": "string",
                    "description": "Optionale Notizen zur Buchung"
                }
            },
            "required": [
                "start_date",
                "end_date",
                "guests"
            ],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "create_booking",
        "description": "Erstellt eine Buchung für das Ferienhaus, wenn der gewünschte Zeitraum verfügbar ist.",
        "parameters": {
            "type": "object",
            "properties": {
                "guest_name": {
                    "type": "string",
                    "description": "Name des Gasts"
                },
                "guest_email": {
                    "type": "string",
                    "description": "E-Mail-Adresse des Gasts"
                },
                "start_date": {
                    "type": "string",
                    "description": "Anreisedatum im ISO-Format YYYY-MM-DD"
                },
                "end_date": {
                    "type": "string",
                    "description": "Abreisedatum im ISO-Format YYYY-MM-DD"
                },
                "guests": {
                    "type": "integer",
                    "description": "Anzahl Gäste"
                },
                "notes": {
                    "type": "string",
                    "description": "Optionale Notizen zur Buchung"
                }
            },
            "required": [
                "guest_name",
                "guest_email",
                "start_date",
                "end_date",
                "guests"
            ],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "get_current_date",
        "description": "Gibt das aktuelle Datum in der Zeitzone Europe/Zurich zurück.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "calculate_date_offset",
        "description": "Berechnet ein Datum relativ zum heutigen Datum, z. B. in 5 Wochen oder in 3 Tagen.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "integer",
                    "description": "Anzahl der Einheiten, z. B. 5"
                },
                "unit": {
                    "type": "string",
                    "enum": ["days", "weeks", "months"],
                    "description": "Zeiteinheit"
                }
            },
            "required": ["amount", "unit"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "show_calendar",
        "description": "Zeigt den Buchungskalender an.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_cancelled": {
                    "type": "boolean",
                    "description": "Ob stornierte Buchungen im Kalender angezeigt werden sollen.",
                }
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "check_availability",
        "description": "Prüft die Verfügbarkeit. Kann entweder einen kompletten Zeitraum prüfen oder freie Zeiträume innerhalb eines Suchzeitraums finden.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Startdatum im ISO-Format YYYY-MM-DD.",
                },
                "end_date": {
                    "type": "string",
                    "description": "Enddatum im ISO-Format YYYY-MM-DD. Exklusiv, wie bei Abreisedaten.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["full_period", "available_periods"],
                    "description": "'full_period' prüft, ob der ganze Zeitraum frei ist. 'available_periods' findet freie Zeiträume innerhalb des Suchzeitraums und ignoriert vergangene Tage.",
                },
            },
            "required": ["start_date", "end_date"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_cancellation_status",
        "description": "Prüft, ob eine Buchung storniert werden kann.",
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "Die Buchungs-ID.",
                }
            },
            "required": ["booking_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "create_region_report",
        "description": "Erstellt einen schön formatierten HTML-Report mit allgemeinen Tipps, Aktivitäten und wissenswerten Informationen für eine Region und einen Reisezeitraum. Nutzt die Interessen des aktuellen Users.",
        "parameters": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "description": "Region oder Ort für den Report.",
                },
                "start_date": {
                    "type": "string",
                    "description": "Startdatum im ISO-Format YYYY-MM-DD.",
                },
                "end_date": {
                    "type": "string",
                    "description": "Enddatum im ISO-Format YYYY-MM-DD.",
                },
            },
            "required": ["region", "start_date", "end_date"],
            "additionalProperties": False,
        },
    },
]


def execute_tool(name: str, arguments: dict, current_user: dict) -> dict:
    if name == "list_bookings":
        return tool_list_bookings(
            include_cancelled=arguments.get("include_cancelled", False),
            start_date=arguments.get("start_date", ""),
            end_date=arguments.get("end_date", ""),
            only_current_user=arguments.get("only_current_user", False),
            current_user=current_user,
        )

    if name == "prepare_booking":
        return tool_prepare_booking(
            guest_name=arguments.get("guest_name", ""),
            guest_email=arguments.get("guest_email", ""),
            start_date=arguments.get("start_date", ""),
            end_date=arguments.get("end_date", ""),
            guests=int(arguments.get("guests") or 0),
            notes=arguments.get("notes", ""),
            current_user=current_user,
        )

    if name == "open_sbb_timetable":
        return tool_open_sbb_timetable(
            from_name=arguments.get("from_name", ""),
            from_id=arguments.get("from_id", ""),
            to_name=arguments.get("to_name", ""),
            to_id=arguments.get("to_id", ""),
            travel_date=arguments.get("travel_date", ""),
            travel_time=arguments.get("travel_time", "08:00"),
            moment=arguments.get("moment", "dep"),
        )

    if name == "get_connections":
        return tool_get_connections(
            from_location=arguments.get("from_location", ""),
            date=arguments.get("date", ""),
            time=arguments.get("time", "08:00"),
            direction=arguments.get("direction", "outbound"),
            limit=int(arguments.get("limit") or 5),
        )

    if name == "get_current_date":
        return tool_get_current_date()

    if name == "calculate_date_offset":
        return tool_calculate_date_offset(
            amount=arguments.get("amount"),
            unit=arguments.get("unit"),
        )

    if name == "show_calendar":
        return tool_show_calendar(
            include_cancelled=arguments.get("include_cancelled", False),
        )

    if name == "check_availability":
        return tool_check_availability(
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            mode=arguments.get("mode", "full_period"),
        )

    if name == "get_cancellation_status":
        return tool_get_cancellation_status(
            booking_id=arguments["booking_id"],
        )

    if name == "create_region_report":
        return tool_create_region_report(
            region=arguments["region"],
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            current_user=current_user,
        )

    return {
        "message": f"Unbekanntes Tool: {name}",
        "artifacts": [],
    }