# Findings

A vet clinic agent that looks up a pet and books a pet taxi (PawsRide). All data is fake.

| Leak | Where the data crossed | Where I closed it | What it still misses |
|---|---|---|---|
| OUT | Booking the taxi sent the whole record to PawsRide | for_partner() only sends 7 needed fields and masks the notes with Comprehend | PawsRide still gets the address and phone, and Comprehend can miss things |
| IN | The pet lookup returns notes with a card number and the owner's mum's details | (not closed) | The model sees it all. Fixing it would slow every lookup and hide useful info |
| STORED | The starter code logged full messages, and my audit log saves messages too | Removed the full logging, and for_storage() runs the guardrail before writing | In testing the guardrail missed a phone number and never masks dates of birth |

**Why each API:** Comprehend for the taxi because the driver needs the phone and address, so I only mask the notes. The guardrail for storage because what can be saved is a policy decision.

**Fail open or fail closed?** Closed. If Comprehend is down nothing is sent, and if the guardrail is down the log says "[withheld]". A failed booking can be retried, but leaked data can't be taken back.
