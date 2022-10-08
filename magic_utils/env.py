import os

try:
    from _env import TOKEN
except ModuleNotFoundError:
    TOKEN = os.environ.get("TOKEN")

POSTGRES_SERVICE = os.environ.get("POSTGRES_SERVICE", "localhost:15444")
FUZZY_THRESHOLD = float(os.environ.get("FUZZY_THRESHOLD", 85))
