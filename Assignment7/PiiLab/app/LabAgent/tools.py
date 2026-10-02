import json
import os
import uuid
from pathlib import Path

from controls import for_partner

PATIENTS = {
    "PET-2201": {
        "patient_ref": "PET-2201",
        "pet_name": "Biscuit",
        "species": "dog",
        "breed": "beagle",
        "owner_name": "Priya Madeup",
        "owner_email": "priya.madeup@example.com",
        "owner_phone": "555-0123",
        "home_address": "7 Pretend Road, Notaville, NV3 4CD",
        "owner_date_of_birth": "1990-05-14",
        "handling_notes": "Nervous in cars, needs a crate.",
        "reception_notes": (
            "Owner paid deposit over phone, card 4111 1111 1111 1111 exp 08/28. "
            "If owner unreachable contact her mum, Sunita Madeup, 555-0188."
        ),
    },
}


def lookup_patient(patient_ref: str) -> dict:
    record = PATIENTS.get(patient_ref.strip().upper())
    if record is None:
        return {"error": f"No patient found with reference {patient_ref!r}."}
    return dict(record)


def _outbox_path() -> Path:
    base = Path(os.environ.get("PIILAB_DATA_DIR", "var"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "pawsride_outbox.jsonl"


def send_to_pawsride(payload: dict) -> str:
    with _outbox_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")
    return f"PR-{uuid.uuid4().hex[:6].upper()}"


def book_pet_taxi(patient_ref: str, pickup_window: str) -> dict:
    record = PATIENTS.get(patient_ref.strip().upper())
    if record is None:
        return {"error": f"No patient found with reference {patient_ref!r}."}

    draft = {
        **record,
        "pickup_window": pickup_window,
        "pickup_address": record["home_address"],
    }
    taxi_ref = send_to_pawsride(for_partner(draft))
    return {"status": "booked", "taxi_ref": taxi_ref}