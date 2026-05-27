import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from loaders import pdf_loader, docx_loader, md_loader
from utils import chunker, claude_client, formatter

DOCS_DIR = Path(__file__).parent / "docs"

LOADERS = {
    ".pdf": pdf_loader.load,
    ".docx": docx_loader.load,
    ".md": md_loader.load,
    ".txt": md_loader.load,
}


def load_docs() -> list[dict]:
    docs = []
    for path in sorted(DOCS_DIR.iterdir()):
        if not path.is_file():
            continue
        loader = LOADERS.get(path.suffix.lower())
        if loader:
            print(f"  Loading {path.name}...")
            docs.append(loader(path))
    return docs


def main():
    print("Document QA — type 'quit' to exit\n")

    docs = load_docs()
    if not docs:
        print(f"No supported files found in {DOCS_DIR}")
        print("Supported formats: .pdf, .docx, .md, .txt")
        print("Drop files into the docs/ folder and run again.")
        sys.exit(1)

    total_chars = sum(len(d["text"]) for d in docs)
    mode = "chunking" if chunker.needs_chunking(docs) else "full-context"
    print(f"\nLoaded {len(docs)} document(s) — {total_chars:,} chars — mode: {mode}\n")

    history = []

    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            print("Goodbye.")
            break

        if mode == "chunking":
            chunks = chunker.retrieve_chunks(docs, question)
            corpus_text = chunker.build_corpus_text_from_chunks(chunks)
        else:
            corpus_text = chunker.build_corpus_text(docs)

        result = claude_client.ask(question, corpus_text, history)
        formatter.print_result(result)


if __name__ == "__main__":
    main()
