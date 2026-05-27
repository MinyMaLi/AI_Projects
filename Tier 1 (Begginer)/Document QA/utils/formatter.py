def print_result(result: dict) -> None:
    cache_info = result.get("_cache_info", "")

    print()
    if result.get("not_found"):
        print("  [Not found in documents]")
        print(f"  {result['answer']}")
        if cache_info:
            print(f"\n  {cache_info.strip()}")
        print()
        return

    print(f"Answer:{cache_info}")
    for line in result["answer"].splitlines():
        print(f"  {line}")

    quotes = result.get("supporting_quotes", [])
    if quotes:
        print("\nSupporting quotes:")
        for i, q in enumerate(quotes, 1):
            print(f"  [{i}] {q['source_document']} ({q['location_hint']})")
            for line in q["quote"].splitlines():
                print(f"      \"{line}\"")
    print()
