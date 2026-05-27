import re


def load(path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = _clean(text)
    return {"filename": path.name, "text": text}


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
