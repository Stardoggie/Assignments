# PiiLab

A vet clinic agent on AgentCore that looks up a pet and books a pet taxi without leaking the owner's personal data. See `FINDINGS.md` for the write-up.

I ran it locally under `agentcore dev`.

## Run the tests

No AWS access needed.

```
pip install -r requirements.txt
pytest
```

## Run the agent

1. Put your guardrail ID in `agentcore/.env.local`:
   ```
   PII_GUARDRAIL_ID=your-guardrail-id
   PII_GUARDRAIL_VERSION=DRAFT
   ```
2. Start the agent:
   ```
   agentcore dev
   ```
3. In another terminal, send it a message:
   ```
   agentcore dev "Hi, I'm Logan Gro (Logan.Gro@example.com, 555-0123). Can you book Lulu, PET-2201, in and arrange a pet taxi for tomorrow 11am?"
   ```

What was sent to the taxi company is in `app/LabAgent/var/pawsride_outbox.jsonl`, and the audit log is in `app/LabAgent/var/audit.jsonl`.
