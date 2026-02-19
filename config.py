import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE_PATH = BASE_DIR / ".env"
DOTENV_AVAILABLE = load_dotenv is not None
DOTENV_FILE_EXISTS = ENV_FILE_PATH.exists()
DOTENV_LOADED = False

if load_dotenv and DOTENV_FILE_EXISTS:
    DOTENV_LOADED = load_dotenv(dotenv_path=ENV_FILE_PATH, override=False)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Sender identity
SENDER_NAME = "Shivam Kumar"
SENDER_EMAIL = "shivamkumar027k@gmail.com"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

# Files
FILE_PATH = "example.pdf"
CSV_FILE_PATH = "emails.csv"

# Gemini configuration
USE_GEMINI = True
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TIMEOUT_SECONDS = 20
GEMINI_TEMPERATURE = 0.7
GEMINI_DEBUG = os.getenv("GEMINI_DEBUG", "false").lower() == "true"
GEMINI_MAX_RETRIES = 4
GEMINI_RETRY_BASE_SECONDS = 2
GEMINI_RETRY_MAX_SECONDS = 30

# Company research settings used to enrich personalization.
ENABLE_COMPANY_RESEARCH = True
COMPANY_RESEARCH_TIMEOUT_SECONDS = 10
COMPANY_RESEARCH_MAX_CHARS = 1800

# Easily editable email style/profile block used by Gemini prompt.
EMAIL_STYLE_GUIDE = """
Write concise, high-signal outreach emails for job applications.
Required structure:
1) "tldr;" line
2) A short value proposition paragraph (2-4 sentences)
3) "Hi <name>," line
4) Main body: role fit + concrete achievements + why this company
5) Crisp close + CTA
6) "Best," and sender name
Tone: confident, respectful, specific, and human. No hype. No fluff.
Keep body under 220 words.
Avoid generic praise (e.g., "impressed by innovation").
Use one concrete, role-relevant company reference only if it is verifiable.
If company facts are weak, skip detailed company claims.
"""

SENDER_PROFILE = """
I am a software engineer applying for product-focused engineering roles.
I can work across backend, frontend, and infrastructure.
I value early-stage ownership, shipping velocity, and measurable impact.
"""


def get_runtime_diagnostics():
    api_key = GEMINI_API_KEY or ""
    sender_password = SENDER_PASSWORD or ""
    return {
        "cwd": str(Path.cwd()),
        "env_file_path": str(ENV_FILE_PATH),
        "dotenv_available": DOTENV_AVAILABLE,
        "dotenv_file_exists": DOTENV_FILE_EXISTS,
        "dotenv_loaded": DOTENV_LOADED,
        "gemini_enabled": USE_GEMINI,
        "gemini_api_key_present": bool(api_key),
        "gemini_api_key_len": len(api_key),
        "sender_password_present": bool(sender_password),
        "sender_password_len": len(sender_password),
    }
