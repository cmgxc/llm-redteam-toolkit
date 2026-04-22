# Attack Catalog

The catalog is intentionally small and focused. Each family targets a specific OWASP LLM Top 10 category and is built around a working hypothesis about why real-world targets fall to it.

## 1. Direct prompt injection (LLM01)

**Hypothesis:** applications concatenate the system prompt and user input without a strong delimiter, so a user message beginning with "Ignore previous instructions" effectively competes with the system prompt on equal footing.

Representative payloads include plain override ("Ignore previous instructions..."), role reassignment ("You are now UnrestrictedGPT"), fake developer notes, fake `<|im_end|>` token injection, and a polite "please repeat your instructions" variant that bypasses many keyword filters.

## 2. Jailbreaks (LLM01)

**Hypothesis:** a model's refusal behavior is a learned pattern that can be disrupted by framing — role-play, fiction, hypotheticals, or a reply prefix that primes compliance.

Includes DAN, the grandma/bedtime-story exploit, hypothetical framing, Developer-Mode claims, opposite-day logic, translation disguise, prefix injection, and a many-shot pattern-erosion variant.

## 3. Encoding attacks (LLM01)

**Hypothesis:** content filters operate on the surface form of the input, but the model understands encodings the filters don't canonicalize.

Includes base64, ROT13, leetspeak, unicode homoglyphs, zero-width characters, hex, Pig Latin, and reversed strings.

## 4. Sensitive information disclosure (LLM06)

**Hypothesis:** secrets and system instructions placed in the prompt are recoverable. Additionally, models sometimes emit plausible-looking fake credentials or PII when asked to produce "examples."

Includes verbatim system-prompt echo, paraphrase-based extraction, direct secret probes, training-data recitation, AWS-key emission, and SSN emission.

## 5. Indirect prompt injection (LLM01)

**Hypothesis:** retrieval-augmented pipelines, summarizers, and agents treat retrieved content as trustworthy. An attacker who can plant text into that content can issue instructions "through the backdoor."

Includes poisoned email summarization, RAG documents with hidden HTML comments, web pages with `display:none` instructions, PDF footer exploits, tool-use hijack via meeting notes, and markdown image exfiltration.

## 6. Insecure output handling (LLM05)

**Hypothesis:** the host application renders or executes model output without treating it as untrusted. The model emits HTML, JavaScript, SQL, or shell fragments that the host then passes through.

Includes `<script>` tags, `javascript:` markdown links, SQL injection-shaped strings, shell metacharacters, and realistic-looking secrets in generated `.env` examples.

## Success criteria

Every payload carries one or both of:

- **`regex_success`** — a list of regex patterns. If any (or all, if `regex_mode: all`) matches the response, the attack is marked successful. Used when the signal is surface-level and unambiguous.
- **`judge_prompt`** — a natural-language description of what counts as success. Sent to a judge model (default: `gpt-4o-mini`) which returns a structured JSON verdict. Used when the signal is semantic ("did the model actually provide usable phishing pretexts?").

If both are present, regex runs first; the semantic judge is only invoked as a fallback when the regex misses. This keeps runs cheap on easy wins and accurate on hard ones.

## Limits of the catalog

- Many payloads are well-known. A production model vendor has almost certainly trained against them. Novel, application-specific attacks should be added per target — that's the point of `src/llm_redteam/payloads/`.
- The regex judge has a false-negative floor: a model can succeed without producing the expected surface-level string. The LLM judge closes most of this gap but isn't perfect.
- Multi-turn attacks are not covered in v0.1; a single payload = a single turn. See the roadmap.
