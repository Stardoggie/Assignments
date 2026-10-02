import os
import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
GUARDRAIL_ID = os.environ.get("PII_GUARDRAIL_ID", "")
GUARDRAIL_VERSION = os.environ.get("PII_GUARDRAIL_VERSION", "DRAFT")

WITHHELD = "[withheld: redaction unavailable]"

def _comprehend():
    return boto3.client("comprehend", region_name=REGION)

def _bedrock_runtime():
    return boto3.client("bedrock-runtime", region_name=REGION)

# Allow-list, not deny-list: a deny-list has to predict every field that will
# ever hold personal data, so a newly added field (e.g. microchip_number) would
# be sent silently. With an allow-list, new fields are withheld by default.
PAWSRIDE_FIELDS = {
    "patient_ref",
    "species",
    "breed",
    "handling_notes",
    "pickup_window",
    "pickup_address",
    "owner_phone",
}

PAWSRIDE_FREE_TEXT = {"handling_notes", "pickup_window"}
def _mask(text: str) -> str:
    resp = _comprehend().detect_pii_entities(Text=text, LanguageCode="en")
    entities = sorted(
        (e for e in resp["Entities"] if e["Type"] != "DATE_TIME"),
        key=lambda e: e["BeginOffset"],
        reverse=True,
    )
    for ent in entities:
        text = text[: ent["BeginOffset"]] + f"[{ent['Type']}]" + text[ent["EndOffset"]:]
    return text

def for_partner(record: dict) -> dict:
    payload = {k: v for k, v in record.items() if k in PAWSRIDE_FIELDS}
    for key in PAWSRIDE_FREE_TEXT:
        if key in payload:
            payload[key] = _mask(payload[key])
    return payload

def for_storage(text: str) -> str:
    if not text:
        return text
    try:
        if not GUARDRAIL_ID:
            raise RuntimeError("PII_GUARDRAIL_ID not set")
        resp = _bedrock_runtime().apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source="OUTPUT",
            content=[{"text": {"text": text}}],
        )
    except Exception:
        return WITHHELD
    if resp.get("action") == "NONE":
        return text
    outputs = resp.get("outputs") or []
    if not outputs or not outputs[0].get("text"):
        return WITHHELD
    return outputs[0]["text"]