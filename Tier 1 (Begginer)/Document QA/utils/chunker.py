from rank_bm25 import BM25Okapi

FULL_CONTEXT_CHAR_LIMIT = 600_000
CHUNK_WORDS = 800
OVERLAP_WORDS = 100
TOP_K = 8


def needs_chunking(docs: list[dict]) -> bool:
    total = sum(len(d["text"]) for d in docs)
    return total >= FULL_CONTEXT_CHAR_LIMIT


def retrieve_chunks(docs: list[dict], query: str, top_k: int = TOP_K) -> list[dict]:
    all_chunks = []
    for doc in docs:
        words = doc["text"].split()
        step = CHUNK_WORDS - OVERLAP_WORDS
        total_chunks = max(1, (len(words) + step - 1) // step)
        for i, start in enumerate(range(0, len(words), step)):
            chunk_words = words[start : start + CHUNK_WORDS]
            all_chunks.append({
                "filename": doc["filename"],
                "chunk_index": i + 1,
                "total_chunks": total_chunks,
                "text": " ".join(chunk_words),
            })

    if not all_chunks:
        return []

    tokenized = [c["text"].lower().split() for c in all_chunks]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(query.lower().split())

    ranked = sorted(range(len(all_chunks)), key=lambda i: scores[i], reverse=True)
    top_indices = sorted(ranked[:top_k])

    return [all_chunks[i] for i in top_indices]


def build_corpus_text(docs: list[dict]) -> str:
    parts = []
    for doc in docs:
        parts.append(f"=== DOCUMENT: {doc['filename']} ===\n{doc['text']}")
    return "\n\n".join(parts)


def build_corpus_text_from_chunks(chunks: list[dict]) -> str:
    parts = []
    for c in chunks:
        header = f"[SOURCE: {c['filename']} | chunk {c['chunk_index']}/{c['total_chunks']}]"
        parts.append(f"{header}\n{c['text']}")
    return "\n\n".join(parts)
