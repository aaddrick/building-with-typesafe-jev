# TypeSafe / Jev API Reference

Snapshot of docs.typesafe.ai taken 2026-09-25 (model `jev-1.13.0`, Python SDK v0.7.1, JS SDK v0.6.0).
The live docs win on any conflict: `https://docs.typesafe.ai/llms.txt`, and append `.md` to any page path.

## HTTP

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer $TYPESAFE_API_KEY
Content-Type: application/json
```

```json
{
  "state": "string | object | array",
  "model": "jev-latest",
  "questions": {
    "<your_id>": { "type": "noul",   "instructions": "...", "criteria": {"true": "...", "false": "..."} },
    "<your_id>": { "type": "choice", "instructions": "...", "criteria": {"opt_a": "desc", "opt_b": null} },
    "<your_id>": { "type": "score",  "instructions": "...", "criteria": ["level 0 desc", "level 1 desc", "level 2 desc"] }
  }
}
```

- Question IDs are yours. The model never sees them. Answers come back under the same IDs.
- `instructions`, every Choice option value, every Score level, and Noul `criteria.true` / `criteria.false` each accept `string | object | array | null` (`EntryType`).
- Noul `criteria` is optional. Choice `criteria` is a map (max 255 options; `null` value = self-explanatory label). Score `criteria` is an ordered array (min 2, max 10 levels; index = level number).

Response:

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "is_urgent":   {"type": "noul", "noul": 0.95},
    "department":  {"type": "choice", "choice": "billing", "confidence": 0.81,
                    "probabilities": {"billing": 0.88, "technical": 0.12, "sales": 0.0}},
    "frustration": {"type": "score", "score": 1.05, "confidence": 0.92,
                    "legend": {"0": "Calm", "1": "Frustrated", "2": "Very angry"},
                    "probabilities": {"0": 0.0, "1": 0.95, "2": 0.05}}
  },
  "usage": {"input_tokens": 304, "output_tokens": 18}
}
```

- `choice` = the highest-probability option. `probabilities` sums to 1.
- `score` = sum of (level × probability). It can fall between levels. HTTP keys levels as strings; the Python SDK keys them as ints.
- `confidence` (Choice and Score only) = a statistic of how peaked `probabilities` is. For a Choice over n options it is `(n·top − 1)/(n − 1)`: 1.0 when all the probability sits on one option, 0 when it is uniform. Score confidence is `1 − Σ pᵢ·|i − top| / U`, clipped at 0, where `top` is the most probable level and `U = ⌊n²/4⌋ / n` is the same sum for a uniform distribution. Probability on an adjacent level costs little, and probability far from `top` costs a lot. The Choice formula is the same idea with every other option at distance 1. Both were fitted on live `jev-1.13.0` answers on 2026-09-26 (Choice: 15 answers; Score: 126 answers with 2–10 levels, mean error 0.006, max 0.026, within the 0.01 rounding of the inputs). The formulas are not documented and may change between versions. Noul has no `confidence`: the `noul` value is the answer and the certainty.
- Every `noul`, probability, and `confidence` is rounded to two decimals.
- `model` = the versioned ID that answered. Log it.

`GET /v1/models` lists aliases (name, description, release_date). Versioned IDs such as `jev-1.13.0` work in `model` even when not listed.

### Errors

| Status | Meaning | Action |
|---|---|---|
| 401 | Missing or bad API key | Fix the `Authorization` header |
| 422 | Body failed validation | Read the body: it names the field |
| 429 | Rate limit | Exponential backoff; honor `retry-after` |
| 529 | Overloaded | Exponential backoff |

The SDKs retry 429/529 by default. Raw HTTP callers must do it themselves.

## Model facts (jev-1.13)

| Item | Value |
|---|---|
| Aliases | `jev-latest` (stable, SDK default), `jev-preview` (currently the same model) |
| Price | $0.042 per million input tokens. Output tokens are free. |
| Rate limits | 250,000 tokens/s, 1,200 requests/min (the docs say these change without notice) |
| Context | 64k tokens for state + all questions; 32k for state + the single longest question |
| Latency | "Most queries complete in about 100 ms" |
| Input | Text only (string, JSON object, array). English is best; other languages work with lower accuracy. |
| Customization | No fine-tuning or LoRA. Shape behavior through state, instructions, and criteria. |
| Data | Not trained on customer requests. ZDR for enterprise. |

Pin `jev-1.13.0` instead of `jev-latest` when you tuned thresholds against that version. An alias moves on a new release and answers can change.

## Python SDK (`typesafe-sdk`, Python >= 3.10)

```bash
uv add typesafe-sdk        # or: pip install typesafe-sdk
export TYPESAFE_API_KEY=...
```

```python
from typesafe_sdk import (
    TypeSafeClient, AsyncTypeSafeClient,
    Choice, Noul, NoulCriteria, Score,
    RetryPolicy, SystemOneResponse, NoulAnswer, ChoiceAnswer, ScoreAnswer,
    TypeSafeError, TypeSafeAPIError, TypeSafeRateLimitError,
)

with TypeSafeClient() as client:                      # model defaults to jev-latest
    r = client.system_one(
        state={"message": "I was charged twice. Please help ASAP."},
        questions={
            "refund": Noul(instructions="Does `message` request a refund?"),
            "repeat": Noul(
                instructions="Has the customer contacted support about this before?",
                criteria=NoulCriteria(true="Mentions a prior attempt or ticket",
                                      false="No sign of previous contact"),
            ),
            "tone": Choice(instructions="What is the customer's tone?",
                           criteria={"calm": None, "frustrated": None, "angry": None}),
            "urgency": Score(instructions="How urgent is this ticket?",
                             criteria=["Can wait a week", "Needs an answer this week",
                                       "Needs an answer today"]),
        },
    )

r.answers["refund"].noul          # all answers, keyed by ID
r.nouls["refund"].noul            # typed views: r.nouls / r.choices / r.scores
r.choices["tone"].choice, r.choices["tone"].confidence, r.choices["tone"].probabilities
r.scores["urgency"].score, r.scores["urgency"].legend   # legend/probabilities keyed by int
r.model, r.usage.input_tokens, r.request_id, r.raw_http_response
```

- Signature: `system_one(state, questions, *, model=None, retry=None, timeout=None, extra_headers=None, extra_body=None, response_model=None)`. `state` and `questions` also work positionally.
- Client: `TypeSafeClient(api_key=None, model=None, retry=None, timeout=None, headers=None, transport=None, http_client=None, base_url=None)`. Default timeout 10.0 s per HTTP operation. A missing key, or one with whitespace or non-printable characters, raises `TypeSafeError` at construction. A wrong key passes construction and raises `TypeSafeAuthenticationError` (401) on the first call.
- Lifecycle: create one client and reuse it for all calls, from threads too. Use `with TypeSafeClient() as client:` for a script. In a service, keep one long-lived client and call `client.close()` at shutdown. Do not create a client per request.
- Async: `async with AsyncTypeSafeClient() as client: r = await client.system_one(...)`.
- Raw dict questions (`{"type": "noul", "instructions": "..."}`) mix freely with objects.
- Typed response: subclass `SystemOneResponse` with fields such as `billing: NoulAnswer`, then pass `response_model=`. Access `r.billing.noul`.
- `RetryPolicy(max_retries, backoff_initial, backoff_max, backoff_jitter, http_statuses, respect_retry_after, api_connection_error, api_timeout_error, exceptions, predicate, timeout)`. `timeout` here is the total retry budget. `RetryPolicy(max_retries=0)` disables retries.
- Exceptions: `TypeSafeError` (base) → `TypeSafeAPIError` (`.status`, `.body`, `.headers`, `.request_id`) → `TypeSafeBadRequestError` 400, `TypeSafeAuthenticationError` 401, `TypeSafePermissionDeniedError` 403, `TypeSafeNotFoundError` 404, `TypeSafeUnprocessableEntityError` 422, `TypeSafeRateLimitError` 429 (`.retry_after_ms`), `TypeSafeInternalServerError` 5xx, `TypeSafeAPIResponseValidationError` (`.field_path`). Separate branch: `TypeSafeAPIConnectionError` → `TypeSafeAPITimeoutError`.
- Env vars: `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL` (default `https://api.typesafe.ai`), `TYPESAFE_DEFAULT_MODEL` (default `jev-latest`), `TYPESAFE_LOG_LEVEL` (`debug|info|warning|error|off`; `debug` logs bodies unredacted).
- Gateways: OpenRouter (`base_url="https://openrouter.ai/api"`, `model="~typesafe/jev-latest"`), Vercel AI Gateway (`base_url="https://ai-gateway.vercel.sh/typesafe"`, `model="typesafe-ai/jev"`).
- v0.6.0 broke `Score.criteria`: it is now an ordered list, not a dict keyed by int. v0.7.0 moved from msgspec to pydantic.

## JavaScript / TypeScript SDK (`@typesafe-ai/sdk`, Node >= 20)

```ts
import { TypeSafeClient, choice, noul, score } from "@typesafe-ai/sdk";

const client = new TypeSafeClient();            // reads TYPESAFE_API_KEY
const { answers, model, usage } = await client.systemOne({
  state: { message: "I was charged twice. Please help ASAP." },
  questions: {
    refund: noul("Does `message` request a refund?"),
    repeat: noul("Has the customer contacted support before?", {
      true: "Mentions a prior attempt or ticket",
      false: "No sign of previous contact",
    }),
    tone: choice("What is the customer's tone?", { calm: null, frustrated: null, angry: null }),
    urgency: score("How urgent is this ticket?", [
      "Can wait a week", "Needs an answer this week", "Needs an answer today",
    ]),
  },
});
answers.tone.choice;   // answer types are inferred from the questions
```

- Helpers: `choice(instructions, criteria)`, `score(instructions, criteria)`, `noul(instructions?, criteria?)`.
- `systemOne(request, options?)`. `request` = `{ state, questions, model? }`. `options` = `{ timeout?, retry?, headers?, signal? }`.
- `TypeSafeClientConfig`: `apiKey`, `baseURL`, `defaultModel`, `defaultHeaders`, `timeout` (ms per attempt, default 10000), `retry` (partial `RetryPolicy`), `logLevel` (default `warn`), `logger`, `fetch`, `dangerouslyAllowBrowser` (default false; true exposes the key).
- `RetryPolicy` defaults: `maxRetries` 2, `backoffInitialMs` 500, `backoffMaxMs` 5000, `backoffJitter` 0.25, `httpStatuses` 408/429/500–599, `respectRetryAfter` true, `maxRetryAfterMs` 60000.
- Errors: `TypeSafeError`, `APIError`, `AuthenticationError`, `BadRequestError`, `PermissionDeniedError`, `NotFoundError`, `UnprocessableEntityError`, `RateLimitError`, `InternalServerError`, `APIConnectionError`, `APITimeoutError`, `APIUserAbortError`.
- `client.models.list()` returns model cards.

## Which live docs page to read

Base: `https://docs.typesafe.ai/`. Append `.md` for Markdown. The full index is `llms.txt`.

| Task | Page |
|---|---|
| The programming model | `concepts/system-one`, `concepts/how-to-build-with-system-one` |
| Ideas by industry | `concepts/use-case-map` |
| Shaping `state` | `concepts/state` |
| Picking a primitive | `primitives`, then `primitives/choice`, `primitives/score`, or `primitives/noul` |
| Object or array instructions and criteria, taxonomy walks | `primitives/advanced` |
| Thresholds and uncertainty | `confidence`, `patterns/confidence-routing` |
| Architectures | `patterns/fan-out`, `patterns/composite-scoring`, `patterns/intent-routing` |
| Known model weak spots | `model-jaggedness/jev-1.13` |
| Limits, aliases, and pricing | `models` |
| HTTP contract | `api` |
| SDK usage and breaking changes | `sdk/python/usage`, `sdk/python/changelog`, `sdk/javascript/changelog` |
| A worked example | `cookbooks/<slug>`. See the index in `patterns.md`. |
