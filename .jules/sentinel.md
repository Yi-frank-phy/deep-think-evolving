## 2024-12-23 - Input Validation on Batch Operations
**Vulnerability:** The `ForceSynthesizeRequest` endpoint accepted an unbounded list of strategy IDs, which could lead to resource exhaustion or log flooding (DoS) if a malicious actor sent a massive list.
**Learning:** Even internal-facing or "HIL" (Human-in-the-Loop) endpoints need strict input validation limits. Logging user input (like a list of IDs) without size limits is a specific risk vector.
**Prevention:** Use Pydantic's `min_length` and `max_length` validators on all list fields in API request models.
