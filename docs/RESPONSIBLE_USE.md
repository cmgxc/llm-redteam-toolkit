# Responsible Use

This toolkit automates adversarial testing of LLM applications. That capability comes with real obligations.

## Do

- Run it against systems you own, operate, or have explicit written authorization to test.
- Use it in pre-production and staging environments where possible.
- Keep reports private by default. A report containing successful attacks is a roadmap for an adversary.
- Disclose findings responsibly to the owner of the target system.

## Don't

- Point the toolkit at third-party hosted LLM applications — even "just to see" — without authorization. That's the same category as running a port scanner against someone else's infrastructure.
- Run payloads that would cost a third party money (token spend, rate-limit exhaustion) on their services.
- Commit reports to public repositories without scrubbing sensitive information — the report contains verbatim responses, which can include leaked secrets or PII.

## On the attack library

The payloads in `src/llm_redteam/payloads/` include prompts that, if they succeed, induce models to produce harmful content (malware scaffolds, phishing pretexts, etc.). They are included because they represent the actual adversarial surface models need to defend against. They are **not** instructions on how to perform harmful acts yourself.

If you extend the catalog, keep the payloads specific to failure modes you intend to *test for*, not to actual capabilities you want the model to gain.

## Data handling

- The `reports/` directory is gitignored by default. Keep it that way.
- If you run against a production system, treat the `report.json` like a pentest deliverable: restricted distribution, retention policy, eventual secure deletion.
- Strongly consider redacting the `response` fields before sharing a report, especially for payloads in the `data_leakage` and `insecure_output` categories.

## Legal

This project is provided under the MIT license. You are responsible for complying with all applicable laws, including computer-fraud / unauthorized-access statutes in your jurisdiction.
