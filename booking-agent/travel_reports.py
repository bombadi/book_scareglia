import json

import requests
from openai import OpenAI

from config import OPENAI_API_KEY, TAVILY_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

REPORT_MODEL = "gpt-4.1-mini"


def search_tavily(query: str, max_results: int = 5) -> list[dict]:
    if not TAVILY_API_KEY:
        return []

    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "include_raw_content": False,
            "max_results": max_results,
        },
        timeout=20,
    )

    response.raise_for_status()

    payload = response.json()
    results = payload.get("results", [])

    return [
        {
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "content": result.get("content", ""),
            "score": result.get("score", 0),
        }
        for result in results
    ]


def build_initial_research_queries(
    region: str,
    start_date: str,
    end_date: str,
    interests: str = "",
) -> list[str]:
    queries = [
        f"{region} aktuelle Veranstaltungen {start_date} {end_date}",
        f"{region} Sehenswürdigkeiten Aktivitäten Reise Tipps",
        f"{region} offizielle Tourismus Informationen",
        f"{region} Restaurants Kulinarik Empfehlungen",
        f"{region} Wandern Natur Ausflüge",
    ]

    if interests:
        queries.append(f"{region} {interests} Empfehlungen Aktivitäten {start_date} {end_date}")

    return queries


def run_tavily_queries(queries: list[str], max_results_per_query: int = 4) -> list[dict]:
    research_results = []

    for query in queries:
        try:
            results = search_tavily(query=query, max_results=max_results_per_query)

            for result in results:
                research_results.append(
                    {
                        "query": query,
                        **result,
                    }
                )

        except requests.RequestException:
            continue

    return deduplicate_research_results(research_results)


def deduplicate_research_results(research_results: list[dict]) -> list[dict]:
    seen_urls = set()
    unique_results = []

    for result in research_results:
        url = result.get("url", "").strip()

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)
        unique_results.append(result)

    return unique_results


def format_research_for_prompt(research_results: list[dict]) -> str:
    if not research_results:
        return "Keine aktuellen Web-Rechercheergebnisse verfügbar."

    lines = []

    for index, result in enumerate(research_results, start=1):
        lines.append(
            f"""
Quelle {index}:
Titel: {result.get("title", "-")}
URL: {result.get("url", "-")}
Suchanfrage: {result.get("query", "-")}
Auszug: {result.get("content", "-")}
""".strip()
        )

    return "\n\n".join(lines)


def reflect_on_research(
    region: str,
    start_date: str,
    end_date: str,
    interests: str,
    research_results: list[dict],
) -> dict:
    research_context = format_research_for_prompt(research_results)

    prompt = f"""
Bewerte die folgende Web-Recherche für einen Reisebericht.

Region:
{region}

Zeitraum:
{start_date} bis {end_date}

Interessen:
{interests or "-"}

Vorhandene Recherche:
{research_context}

Aufgabe:
Prüfe, ob die Recherche ausreichend ist für:
- aktuelle oder saisonale Aktivitäten
- offizielle Tourismusinformationen
- Ausflüge und Natur
- Kulinarik
- Empfehlungen passend zu den Interessen
- seriöse Quellen

Gib ausschließlich valides JSON zurück, ohne Markdown.

JSON-Format:
{{
  "is_sufficient": true,
  "missing_topics": ["..."],
  "additional_queries": ["..."]
}}

Regeln:
- additional_queries maximal 4 Einträge.
- Verwende konkrete Suchanfragen.
- Wenn die Recherche ausreichend ist, additional_queries leer lassen.
"""

    response = client.responses.create(
        model=REPORT_MODEL,
        input=[
            {
                "role": "system",
                "content": "Du bist ein Recherche-Reviewer. Du antwortest ausschließlich mit validem JSON.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    raw_text = response.output_text.strip()

    try:
        reflection = json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "is_sufficient": True,
            "missing_topics": [],
            "additional_queries": [],
        }

    return {
        "is_sufficient": bool(reflection.get("is_sufficient", True)),
        "missing_topics": reflection.get("missing_topics", [])[:6],
        "additional_queries": reflection.get("additional_queries", [])[:4],
    }


def collect_region_research_with_reflection(
    region: str,
    start_date: str,
    end_date: str,
    interests: str = "",
) -> dict:
    initial_queries = build_initial_research_queries(
        region=region,
        start_date=start_date,
        end_date=end_date,
        interests=interests,
    )

    initial_results = run_tavily_queries(
        queries=initial_queries,
        max_results_per_query=4,
    )

    reflection = reflect_on_research(
        region=region,
        start_date=start_date,
        end_date=end_date,
        interests=interests,
        research_results=initial_results,
    )

    additional_queries = reflection.get("additional_queries", [])

    additional_results = []

    if additional_queries:
        additional_results = run_tavily_queries(
            queries=additional_queries,
            max_results_per_query=4,
        )

    combined_results = deduplicate_research_results(
        [
            *initial_results,
            *additional_results,
        ]
    )

    return {
        "results": combined_results[:14],
        "initial_queries": initial_queries,
        "additional_queries": additional_queries,
        "reflection": reflection,
    }


def create_region_report_html(
    region: str,
    start_date: str,
    end_date: str,
    interests: str = "",
    guest_name: str = "",
) -> dict:
    research = collect_region_research_with_reflection(
        region=region,
        start_date=start_date,
        end_date=end_date,
        interests=interests,
    )

    research_results = research["results"]
    research_context = format_research_for_prompt(research_results)

    prompt = f"""
Erstelle einen stilvollen, hilfreichen HTML-Reisebericht für einen Ferienhaus-Aufenthalt.

Region:
{region}

Zeitraum:
{start_date} bis {end_date}

Name des Users:
{guest_name or "-"}

Interessen des Users:
{interests or "-"}

Aktuelle Web-Recherche:
{research_context}

Reflection-Ergebnis:
{json.dumps(research["reflection"], ensure_ascii=False)}

Inhalt:
- Kurze freundliche Einleitung
- Überblick zur Region
- Empfehlungen passend zu den Interessen
- Aktuelle oder saisonale Aktivitäten im Zeitraum, sofern durch die Web-Recherche gestützt
- Wissenswertes für den Aufenthalt
- Tipps für Familien, Kulinarik, Natur und Ausflüge, wenn passend
- Eine kurze Checkliste
- Einen Abschnitt "Geprüfte Quellen" mit anklickbaren Links zu den verwendeten Quellen

Wichtige Regeln:
- Nutze aktuelle Informationen nur, wenn sie in der Web-Recherche enthalten sind.
- Erfinde keine konkreten tagesaktuellen Veranstaltungen, Uhrzeiten, Preise oder Öffnungszeiten.
- Wenn Events, Preise oder Öffnungszeiten relevant sind, formuliere vorsichtig und empfehle, die verlinkte Quelle vor dem Besuch zu prüfen.
- Gib keine externen Quellen vor, die nicht in der Web-Recherche enthalten sind.
- Verlinke Quellen nur mit URLs aus der Web-Recherche.
- Ausgabe ausschließlich als vollständiges HTML-Fragment.
- Kein Markdown.
- Keine ``` Code fences.
- Das HTML soll inline CSS enthalten und schön als E-Mail/Artifact funktionieren.
- Verwende ein modernes, freundliches Design mit Karten, Badges und klaren Abschnitten.
"""

    response = client.responses.create(
        model=REPORT_MODEL,
        input=[
            {
                "role": "system",
                "content": "Du bist ein hilfreicher Reiseassistent und erzeugst sauberes, schönes HTML auf Basis der bereitgestellten Recherchequellen.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    html = response.output_text.strip()

    return {
        "title": f"Region-Report: {region}",
        "html": html,
        "region": region,
        "start_date": start_date,
        "end_date": end_date,
        "sources": research_results,
        "reflection": research["reflection"],
        "initial_queries": research["initial_queries"],
        "additional_queries": research["additional_queries"],
    }