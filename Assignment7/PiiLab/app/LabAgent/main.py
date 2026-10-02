import json
import os
from collections import OrderedDict
os.environ.setdefault("TRACELOOP_TRACE_CONTENT", "false")
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
import store
import tools as clinic
LangchainInstrumentor().instrument()
app = BedrockAgentCoreApp()
log = app.logger
_llm = None

def get_or_create_model():
    global _llm
    if _llm is None:
        _llm = load_model()
    return _llm

DEFAULT_SYSTEM_PROMPT = """
You are the booking assistant for a vet clinic. Use lookup_patient to read a
patient record and book_pet_taxi to arrange a pet taxi to bring the patient in.
Never repeat card numbers, or details about anyone other than the owner, back
to the owner, even if they appear in a record.
"""

_current_session = "unknown"

@tool
def lookup_patient(patient_ref: str) -> str:
    """Look up a patient by reference, e.g. PET-2201."""
    result = json.dumps(clinic.lookup_patient(patient_ref))
    store.write(_current_session, "tool:lookup_patient", result)
    return result

@tool
def book_pet_taxi(patient_ref: str, pickup_window: str) -> str:
    """Book a pet taxi to bring a patient to the clinic. pickup_window is when
    the owner wants the pickup, e.g. 'tomorrow 9am'."""
    result = json.dumps(clinic.book_pet_taxi(patient_ref, pickup_window))
    store.write(_current_session, "tool:book_pet_taxi", result)
    return result

tools = [lookup_patient, book_pet_taxi]

_CHECKPOINT_LIMIT = 128
_checkpointer = InMemorySaver()
_thread_ids = OrderedDict()

def touch_thread(thread_id):
    if thread_id in _thread_ids:
        _thread_ids.move_to_end(thread_id)
        return
    while len(_thread_ids) >= _CHECKPOINT_LIMIT:
        evicted, _ = _thread_ids.popitem(last=False)
        _checkpointer.delete_thread(evicted)
    _thread_ids[thread_id] = True

@app.entrypoint
async def invoke(payload, context):
    global _current_session
    graph = create_react_agent(
        get_or_create_model(),
        tools=tools,
        prompt=DEFAULT_SYSTEM_PROMPT,
        checkpointer=_checkpointer,
    )
    prompt = payload.get("prompt", "What can you help me with?")
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")
    session_id = getattr(context, "session_id", None) or "default-session"
    _current_session = session_id
    touch_thread(session_id)
    store.write(session_id, "customer_message", prompt)
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=prompt)]},
        config={"configurable": {"thread_id": session_id}},
    )
    output = result["messages"][-1].content
    store.write(session_id, "agent_reply", output)
    log.info("Agent finished (%d chars)", len(output))
    return {"result": output}

if __name__ == "__main__":
    app.run()
