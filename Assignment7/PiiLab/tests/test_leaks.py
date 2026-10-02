import json
import pytest
import store
import tools

RECORD = tools.PATIENTS["PET-2201"]
EMAIL = RECORD["owner_email"]
NEVER_SENT = [
    EMAIL,
    RECORD["owner_name"],
    RECORD["owner_date_of_birth"],
    "4111 1111 1111 1111",
    "Sunita Madeup",
    "555-0188",
]
NEVER_STORED = NEVER_SENT[:2] + NEVER_SENT[3:] + [RECORD["owner_phone"], RECORD["home_address"]]

def read_lines(path):
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []

def test_pawsride_payload_has_no_raw_personal_data(offline):
    result = tools.book_pet_taxi("PET-2201", f"tomorrow 9am, email me at {EMAIL}")
    assert result["status"] == "booked"
    sent = read_lines(offline / "pawsride_outbox.jsonl")
    assert len(sent) == 1
    for secret in NEVER_SENT:
        assert secret not in sent[0], f"{secret!r} was sent to PawsRide"
    payload = json.loads(sent[0])
    assert payload["owner_phone"] == RECORD["owner_phone"]
    assert payload["pickup_address"] == RECORD["home_address"]
    assert "tomorrow" in payload["pickup_window"]

def test_nothing_sent_when_comprehend_is_down(offline, comprehend_down):
    with pytest.raises(ConnectionError):
        tools.book_pet_taxi("PET-2201", "tomorrow 9am")
    assert read_lines(offline / "pawsride_outbox.jsonl") == []

def test_stored_record_has_no_raw_personal_data(offline):
    store.write("s1", "tool:lookup_patient", json.dumps(tools.lookup_patient("PET-2201")))
    store.write("s1", "customer_message", f"Hi, I'm {RECORD['owner_name']} ({EMAIL}), PET-2201.")
    written = (offline / "audit.jsonl").read_text(encoding="utf-8")
    assert len(written.splitlines()) == 2
    for secret in NEVER_STORED:
        assert secret not in written, f"{secret!r} was written to disk"
    assert "PET-2201" in written

def test_storage_fails_closed_when_guardrail_is_down(offline, guardrail_down):
    store.write("s1", "customer_message", f"my email is {EMAIL}")
    written = (offline / "audit.jsonl").read_text(encoding="utf-8")
    assert EMAIL not in written
    assert "withheld" in written
