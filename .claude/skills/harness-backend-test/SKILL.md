---
name: harness-backend-test
description: Guidance for backend test generation steps under the harness flow.
---

# Backend Test Generation

- Encode the approved test cases and spec faithfully. Do not expand scope or add speculative coverage.
- Treat the approved test cases as the only source of test scope. Use the spec only to resolve expected values or terminology.
- Treat this as a code generation step, not a repository audit step.
- Replace the primary target test file early in the turn. If a harness placeholder exists, overwrite it immediately.
- Avoid broad repository exploration. Read the target implementation file only when you must confirm the import path or public interface.
- Do not stop after deciding existing tests look comprehensive. The required output for this step is an updated concrete test file in the target path.
- Prefer one test per approved case and assert the exact contract required by the spec, including return shape and output formatting when those are part of the contract.
- Do not add speculative tests from the spec alone, and do not split one approved case into multiple test functions unless the case itself explicitly requires multiple intents.
- Keep generated tests lint-safe. Avoid `try`-`except`-`pass`, broad exception swallowing, or other patterns that a normal backend lint gate would reject.
