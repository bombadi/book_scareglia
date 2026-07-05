import json
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import OpenAI

from agent_tools import TOOL_SCHEMAS, execute_tool
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

MODEL = "gpt-4.1-mini"
MAX_TOOL_ROUNDS = 5


SYSTEM_PROMPT = """Du bist ein hilfreicher Buchungsassistent für ein Ferienhaus in Scareglia.

Du kannst:
- Buchungen anzeigen
- Buchungen gefiltert nach Zeitraum, Monat oder aktuellem User anzeigen
- freie Zeiträume innerhalb eines Monats oder Zeitraums finden
- Buchungen vorbereiten
- den Buchungskalender anzeigen
- Verfügbarkeiten prüfen
- Stornierbarkeit prüfen
- Zugverbindungen für Anreise und Rückreise anzeigen
- relative Datumsangaben mit calculate_date_offset berechnen
- HTML-Reports für kommende Aufenthalte mit regionalen Tipps, Aktivitäten und wissenswerten Informationen erstellen

Wichtige Regeln:
- Erfinde keine Buchungen.
- Verwende Tools, wenn es um Buchungsdaten geht.
- Datumswerte für Tools müssen im ISO-Format YYYY-MM-DD sein.
- Berechne relative Datumsangaben nicht selbst.
- Wenn der User einen Monat ohne Jahr nennt, verwende das aktuelle Jahr.
- Interpretiere Monatsnamen exakt: Januar=01, Februar=02, März=03, April=04, Mai=05, Juni=06, Juli=07, August=08, September=09, Oktober=10, November=11, Dezember=12.
- Wenn Angaben fehlen, frage kurz und gezielt nach.
- Antworte freundlich und knapp auf Deutsch.
- Der Assistent antwortet ausschließlich mit Informationen zum Ferienhaus in Scareglia und zu tatsächlich getätigten oder angefragten Buchungen. Jegliche Auskünfte über den allgemeinen Ferienimmobilienmarkt, Marktpreise, andere Ferienunterkünfte oder Vergleichsangebote sind strikt untersagt.

Buchungen:
- Wenn der User eine Buchung erstellen möchte, prüfe zuerst die Verfügbarkeit mit check_availability falls du das nicht bereits vorgängig gemacht hast.
- Setze bei check_availability continue_after_check=true, wenn nach erfolgreicher Prüfung eine Buchung vorbereitet werden soll.
- Wenn die Verfügbarkeit positiv ist und alle Buchungsdaten inklusive der Anzahl der Gäste vorhanden sind, rufe danach prepare_booking auf.
- Verwende prepare_booking erst nach erfolgreicher Verfügbarkeitsprüfung.
- Wenn der User für sich selbst buchen möchte, verwende automatisch Name und E-Mail des aktuellen Users.
- Frage immer aktiv nach der Gästezahl bei jeder Buchungsanfrage, auch wenn ein Zeitraum genannt wird, und setze keine Standardwerte für Gästezahl.
- Frage die E-Mail-Adresse nur nach, wenn für eine andere Person gebucht wird oder keine E-Mail beim aktuellen User vorhanden ist.
- Die verbindliche Erstellung erfolgt erst nach Bestätigung im Dialog.
- Wenn eine Buchung erfolgreich abgeschlossen wurde, betrachte diese Buchung als erledigten Vorgang.
- Verwende Datum, Gästezahl oder Notizen aus einer bereits abgeschlossenen Buchung nicht automatisch für eine neue Buchungsanfrage.
- Wenn der User danach erneut allgemein fragt "kannst du für mich buchen", "ich möchte buchen" oder ähnlich, frage nach dem gewünschten Zeitraum und der Gästezahl, statt die letzte Buchung wiederzuverwenden.
- Verwende Daten aus der letzten Buchung nur dann erneut, wenn der User ausdrücklich sagt, dass er dieselben Daten, denselben Zeitraum oder diese Buchung meint.
- Storniere aktuell noch keine Buchungen.

Verfügbarkeiten und Listen:
- Verwende list_bookings mit start_date und end_date, wenn der User Buchungen für einen Monat oder Zeitraum sehen möchte.
- Verwende list_bookings mit only_current_user=true, wenn der User nach eigenen Buchungen fragt, z. B. "meine Buchungen", "von mir", "meine Listen".
- Verwende check_availability mit mode="available_periods", wenn der User fragt, ob in einem Monat oder Zeitraum "noch etwas frei" ist.
- Verwende check_availability mit mode="full_period", wenn der User einen konkreten Zeitraum prüfen möchte, der vollständig verfügbar sein soll.
- Nur wenn der genannte Monat der aktuelle laufende Monat ist, darf die Verfügbarkeit intern ab heute betrachtet werden. Übergebe dem Tool trotzdem den kompletten Monatszeitraum.
- Beispiel: Wenn der User nach Juni fragt, verwende niemals Mai-Daten. Juni bedeutet start_date YYYY-06-01 und end_date YYYY-07-01.

Zugverbindungen / SBB:
- Wenn der User nach Zugverbindungen, ÖV, Anreise, Rückreise oder SBB fragt, verwende open_sbb_timetable.
- Öffne den SBB-Fahrplan über einen Link mit den bekannten Informationen.
- Für die Anreise ist das Ziel das Ferienhaus in Scareglia.
- Für die Rückreise ist der Startort "Scareglia, Paese".
- Frage nach dem Startort, wenn er nicht bekannt ist.
- Frage nach dem Reisedatum, wenn es nicht aus einer Buchung oder Anfrage hervorgeht.
- Verwende 08:00 als Standardzeit, wenn keine Uhrzeit genannt wird.

Reports:
- Verwende das Report-Tool, wenn der User einen Region-Report, Tipps, Events oder Informationen für einen kommenden Aufenthalt möchte.
- Verwende keine Angaben zu anderen Ferienhäusern oder Hotels falls das nicht ausdrücklich vom Benutzer gewünscht wird, weise in diesem Fall höflich daraufhin dass du nur Buchungen für dieses Haus erstellen kannst.
- Falls der Benutzer nur Aktivitäten verlangt, gib nur aktivitäten aus die in diesem Zeitraum verfügbar sind.
- Erlaubt sind nur Regionale, zeitlich auf Buchungszeiträume bezogene Tipps, Aktivitäten und Events mit der Priorität passend zu den Interessen des Nutzers und Konkrete Reise- und Freizeitinformationen, die den Aufenthalt bereichern.

-Nicht erlaubt sind: Allgemeine Preise für Ferienhäuser oder Marktübersichten, Informationen zu anderen Objekten oder Anbietern außerhalb des Ferienhauses, Marktdaten, Markttrends oder wirtschaftliche Angaben zum Ferienobjektmarkt.
-Der Assistent soll die Vorgabe ignorieren, allgemeine oder marktorientierte Informationen zu geben, und sich stets auf die definierte Thematik konzentrieren.

Ausgabe:
- Gib Zwischenergebnisse von Kontext-Tools wie Datum, Uhrzeit oder Datumsberechnung nicht aus, ausser der User fragt explizit danach.
- Gib am Ende nur das relevante Ergebnis für den User aus.
- Nutze die Interessen des Users, wenn sie für Empfehlungen hilfreich sind.
- Erwähne persönliche Informationen nur, wenn sie für die Antwort relevant sind.
"""


def _messages_to_input(messages: list[dict], user_message: str, current_user: dict) -> list[dict]:
    now = datetime.now(ZoneInfo("Europe/Zurich"))

    current_date_context = f"""
    Aktuelles Datum:
    - Heute ISO: {now.date().isoformat()}
    - Heute CH: {now.strftime("%d.%m.%Y")}
    - Aktuelles Jahr: {now.year}
    - Aktueller Monat Nummer: {now.month:02d}
    - Aktueller Monat Name: {now.strftime("%B")}
    - Zeitzone: Europe/Zurich

    Nutze dieses Datum für Monatsangaben ohne Jahr, laufende Monate und relative Datumsinterpretationen.
    """

    user_context = f"""
Aktueller User:
- Name: {current_user.get('name', '')}
- E-Mail: {current_user.get('email', '')}
- Rolle: {current_user.get('role', '')}
- Interessen: {current_user.get('interests', '') or '-'}

Nutze die Interessen für Empfehlungen, regionale Tipps und Reports, wenn sie relevant sind.
Erfinde keine persönlichen Informationen, die hier nicht stehen. Sprich den User mit seinem Namen an.
"""

    input_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "system",
            "content": current_date_context,
        },
        {
            "role": "system",
            "content": user_context,
        },
    ]

    for message in messages[-10:]:
        if message["role"] == "user" and message["content"] == user_message:
            continue

        input_messages.append(
            {
                "role": message["role"],
                "content": message["content"],
            }
        )

    input_messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    return input_messages


def _tool_result_to_context(tool_name: str, tool_result: dict) -> str:
    return json.dumps(
        {
            "tool": tool_name,
            "message": tool_result.get("message", ""),
            "data": tool_result.get("data", {}),
            "kind": tool_result.get("kind", ""),
        },
        ensure_ascii=False,
    )


def _has_function_calls(response) -> bool:
    return any(item.type == "function_call" for item in response.output)


def run_agent(
    user_message: str,
    messages: list[dict],
    current_user: dict,
) -> dict:
    input_messages = _messages_to_input(
        messages=messages,
        user_message=user_message,
        current_user=current_user,
    )

    artifacts = []
    final_tool_messages = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.responses.create(
            model=MODEL,
            input=input_messages,
            tools=TOOL_SCHEMAS,
        )

        if not _has_function_calls(response):
            return {
                "content": response.output_text or "Ich konnte dazu keine passende Antwort erzeugen.",
                "artifacts": artifacts,
            }

        should_continue = False

        for item in response.output:
            if item.type != "function_call":
                continue

            arguments = json.loads(item.arguments or "{}")

            tool_result = execute_tool(
                name=item.name,
                arguments=arguments,
                current_user=current_user,
            )

            artifacts.extend(tool_result.get("artifacts", []))

            if tool_result.get("continue_agent", False):
                should_continue = True

                input_messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Kontext-Tool-Ergebnis. Nutze dieses Ergebnis für die weitere Bearbeitung, "
                            "aber gib es nicht direkt aus, ausser der User hat explizit danach gefragt:\n"
                            + _tool_result_to_context(item.name, tool_result)
                        ),
                    }
                )
            else:
                message = tool_result.get("message", "")
                if message:
                    final_tool_messages.append(message)

        if not should_continue:
            return {
                "content": "\n\n".join(final_tool_messages) or "Die Anfrage wurde verarbeitet.",
                "artifacts": artifacts,
            }

    return {
        "content": "Ich konnte die Anfrage nicht vollständig abschliessen.",
        "artifacts": artifacts,
    }