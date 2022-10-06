import unicodedata


def _strip_accents(s: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def treat_string(s: str) -> str:
    return _strip_accents(s.split("//")[0].strip().lower())
