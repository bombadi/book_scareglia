import os


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value

def get_optional_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


GOOGLE_SHEET_ID = get_required_env("GOOGLE_SHEET_ID")
GOOGLE_SERVICE_ACCOUNT_FILE = get_optional_env("GOOGLE_SERVICE_ACCOUNT_FILE")

OPENAI_API_KEY = get_required_env("OPENAI_API_KEY")
TAVILY_API_KEY = get_optional_env("TAVILY_API_KEY")

GMAIL_SENDER_EMAIL = get_optional_env("GMAIL_SENDER_EMAIL")
GMAIL_FROM_EMAIL = get_optional_env("GMAIL_FROM_EMAIL")
APP_BASE_URL = get_optional_env("APP_BASE_URL", "http://localhost:8501")