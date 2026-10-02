import re
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app" / "LabAgent"))
import controls

PATTERNS = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("CREDIT_DEBIT_NUMBER", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("PHONE", re.compile(r"\b555-01\d\d\b")),
    ("ADDRESS", re.compile(r"\b\d+ \w+ (?:Road|Street|Lane), \w+, [A-Z]{2}\d \d[A-Z]{2}\b")),
    ("NAME", re.compile(r"\b(?:Priya|Sunita) Madeup\b")),
]

def find_pii(text):
    hits = []
    for etype, rx in PATTERNS:
        for m in rx.finditer(text):
            hits.append({"Type": etype, "BeginOffset": m.start(), "EndOffset": m.end(), "Score": 0.99})
    return hits

class FakeComprehend:
    def detect_pii_entities(self, Text, LanguageCode):
        return {"Entities": find_pii(Text)}

class FakeGuardrail:
    def apply_guardrail(self, guardrailIdentifier, guardrailVersion, source, content):
        text = content[0]["text"]["text"]
        hits = sorted(find_pii(text), key=lambda h: h["BeginOffset"], reverse=True)
        if not hits:
            return {"action": "NONE", "outputs": []}
        for h in hits:
            text = text[: h["BeginOffset"]] + "{" + h["Type"] + "}" + text[h["EndOffset"]:]
        return {"action": "GUARDRAIL_INTERVENED", "outputs": [{"text": text}]}

class Down:
    def __getattr__(self, name):
        def fail(*args, **kwargs):
            raise ConnectionError("service unavailable")
        return fail

@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setenv("PIILAB_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(controls, "GUARDRAIL_ID", "fake-guardrail")
    monkeypatch.setattr(controls, "_comprehend", lambda: FakeComprehend())
    monkeypatch.setattr(controls, "_bedrock_runtime", lambda: FakeGuardrail())
    return tmp_path

@pytest.fixture
def comprehend_down(monkeypatch):
    monkeypatch.setattr(controls, "_comprehend", lambda: Down())

@pytest.fixture
def guardrail_down(monkeypatch):
    monkeypatch.setattr(controls, "_bedrock_runtime", lambda: Down())
