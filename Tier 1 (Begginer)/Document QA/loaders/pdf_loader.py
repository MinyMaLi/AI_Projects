import re
import fitz  # PyMuPDF


def load(path) -> dict:
    doc = fitz.open(str(path))
    pages = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()
    text = _clean("\n\n".join(pages))
    return {"filename": path.name, "text": text}


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
