from ticket_assistant.retriever import load_runbook_chunks


def test_runbooks_load_and_split():
    chunks = load_runbook_chunks()

    assert len(chunks) == 18
    assert all(chunk.page_content.strip() for chunk in chunks)
    assert all("source" in chunk.metadata for chunk in chunks)


def test_all_runbook_files_are_loaded():
    chunks = load_runbook_chunks()

    sources = {
        chunk.metadata["source"]
        for chunk in chunks
    }
    assert sources == {
        "account-and-billing.md",
        "known-issues.md",
        "refund-policy.md",
        "shipping-policy.md"
    }