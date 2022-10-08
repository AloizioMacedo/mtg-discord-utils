import os

try:
    from _env import TOKEN
except ModuleNotFoundError:
    TOKEN = os.environ.get("TOKEN")

_POSTGRES_SERVICE = os.environ.get("POSTGRES_SERVICE", "localhost:15444")
POSTGRES_CONNECTION_URL = os.environ.get(
    "POSTGRES_CONNECTION_URL",
    f"postgresql://postgres:postgres@{_POSTGRES_SERVICE}/postgres",
)
FUZZY_THRESHOLD = float(os.environ.get("FUZZY_THRESHOLD", 85))
