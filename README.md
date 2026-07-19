# The Negotiator

> Voice agents that call, compare, and haggle - pick your market, never overpay again.

The Negotiator is an end-to-end voice-agent system that gathers real prices by phone, reports them in comparable form, and negotiates the best deal for any phone-priced market. An intake agent builds one structured, user-confirmed job spec from a voice interview or documents, then a caller agent runs live calls against distinct negotiation styles, extracts itemized quotes, and haggles using only honest leverage - a real benchmark or a previously verified quote. Every call ends in a structured outcome, and the system delivers a ranked recommendation backed by transcripts, recordings, and red-flag checks. Switching verticals - moving, contractor bids, medical bills, auto repair - is a config change, not a rewrite.

---

## 1. Problem & Challenge

In many markets the real price is only available by phone - moving, contractor bids, auto repair, medical bills, freight, equipment rental, wedding vendors. These are fragmented, phone-and-paper industries where the fair price exists, but nobody has the time to extract it. Getting it means calling 5-8 operators, describing the same job identically every time, sitting through hold music, comparing fee structures that are deliberately hard to compare, and negotiating. Almost nobody does this.

The same three structural failures repeat across every one of these verticals:

- **Opaque pricing** - quotes for identical work vary wildly, and the only sanity check available to a buyer is gathering multiple quotes. There is no efficient way to do it today.
- **Unreliable estimates** - a price given without full context is routinely a lowball that inflates on the invoice. Lowball-then-upcharge is a business model, not an accident.
- **No way to shop around** - supply is thousands of small operators reachable one phone call at a time, so buyers settle for one or two quotes and hope.

Moving is simply the best-documented case: real quotes for one identical 45-mile move ranged from **$1,158 to $6,506** (a **5.6x spread** for the same work), sight-unseen phone quotes are **40% more likely** to end above the original bill (FMCSA), and the BBB logs **13,000+ complaints/year**, mostly over surprise price hikes.

This is not a data problem - the prices and red-flag rules already exist. What is missing is anyone with the time and stamina to extract those numbers, one call at a time. **The Negotiator closes that gap for any phone-priced market: for the first time, software literally picks up the phone, compares, and haggles - and switching verticals is a config change, not a rewrite.**

## 2. Target Audience

- **Primary (B2C):** Individuals facing an infrequent, high-stakes, phone-priced purchase with no time to comparison-shop - e.g. someone like *Daniel*, 34, three weeks to moving day, who would otherwise take a sight-unseen quote from the friendliest of two calls and hope.
- **The market being called:** ~28M Americans move every year; the supply side is 16,851 movers averaging 6.2 employees - phone-and-paper operations that will never adopt quoting software but always answer the phone.
- **Generalizes beyond moving:** any market where the real price is only available by phone - contractor bids, auto repair, medical bills, freight, equipment rental, wedding vendors. The vertical is configuration, not code.

## 3. Solution & Core Features

An end-to-end voice-agent system that runs the mandatory loop **intake -> calls -> negotiation -> ranked recommendation**, built on two ElevenLabs voice agents plus one control-plane/MCP server.

- **Agent 1 - Estimator (Intake):** conducts a voice interview covering everything a professional estimator would ask (route, dates, budget, service type, loaders, rooms/inventory/large items, floors/stairs/elevators/long-carry/parking). Also ingests at least one document type (machine-readable inventory PDF or existing quote) into the *same* `MoveSpec` JSON with field-level provenance. The user confirms the full spec before any call is made.
- **Explicit, separate consent:** no call job is created until a versioned `OutreachConsent` exists (scope, max carriers, allowed call window with timestamp) - separate from the order confirmation.
- **Orchestrator:** discovers/validates carriers (local demo dataset, FMCSA validation fixture, Exa fallback), pulls a dated moveBuddha benchmark, and computes per-carrier call windows across IANA timezones + opening hours.
- **Agent 2 - Caller/Closer:** receives an immutable spec snapshot, benchmark, and one carrier, extracts an itemized quote, and honestly negotiates using only real leverage. Demo runs against three distinct styles via a human-in-the-loop carrier console: tough negotiator, hidden-fee lowballer, hard-sell/stonewaller.
- **Structured outcomes + reporting:** every call ends in exactly one terminal state (`itemized_quote`, `callback_commitment`, `documented_decline`, `no_answer`, `technical_failure`). A dashboard shows a ranked comparison with initial->final totals, itemized fees, binding/deposit/validity, benchmark position, red flags, and links to transcripts and recordings.

## 4. Unique Selling Proposition (USP)

- **Real negotiation, not a screenplay.** Prices move during live calls because of leverage the agent actually gathered - a real benchmark or a previously verified quote - never because a script said so. Calls are sequenced (`concurrency = 1`) precisely so competing-bid leverage is causally honest.
- **Honesty is enforced, not just prompted.** The agent never invents inventory, urgency, or a fake bid; a benchmark is presented as a market reference, and a competing bid is only cited when a real `verified_quote` exists. These constraints are backed by server-side role allowlists and per-call signed capabilities, not prompt text alone.
- **Comparable by construction.** One confirmed, immutable spec is reused verbatim across every call, so quotes are genuinely comparable - itemized fees, included/excluded services, binding status.
- **Trust on both ends of the line.** AI disclosure, graceful handling of "are you a robot?", barge-in, and evasive dispatchers are covered by dedicated prompt examples and golden-call evals.
- **Red-flag integrity.** A quote 30%+ below benchmark low is flagged `suspicious_lowball` - never auto-selected as the winner.
- **Vertical-agnostic.** Swapping movers for auto body shops means swapping a config file (taxonomy, benchmarks, red-flag rules, negotiation levers), not rewriting agents.

## 5. Implementation & Technology

- **Voice agents:** two private ElevenLabs Agents; `@elevenlabs/react` for the intake session and the carrier console (browser voice session for the demo, with a feature-flagged Twilio/SIP outbound adapter for real PSTN calls - off by default).
- **Control plane:** Fastify + official TypeScript MCP SDK exposing one Streamable HTTP `/mcp` endpoint, REST API, ElevenLabs webhooks, and a scheduler/dispatcher - a single process.
- **MCP security:** one server registered twice (Agent 1 / Agent 2) with distinct scoped credentials and tool allowlists; per-session short-lived signed capabilities carry `move_id`, `spec_version`, `call_id`, `carrier_id`, `consent_id`. The server derives scope from verified credentials, never from LLM-supplied arguments.
- **Contracts & schemas:** shared Zod `contracts` package (`MoveSpec`, `Carrier`, `Benchmark`, `CallOutcome`, `Quote`) used by MCP tools, REST, prompts, and UI.
- **Storage & queue:** SQLite + Drizzle (repository interface allows a PostgreSQL migration); a `call_jobs` table with lease/heartbeat worker and CAS/nonce guards - no Redis, no double dispatch.
- **Data sources:** deterministic local carrier dataset (primary), FMCSA validation fixture, Exa `POST /search` (`category: company`) fallback, dated moveBuddha benchmark fixtures with provenance (no scraping; `unavailable` state when no match).
- **Timezones:** address -> coordinates -> IANA timezone pipeline; business-hours intersect user-window intersect compliance-window, DST/overnight-aware; no dispatch on unknown data.
- **Reliability:** HMAC-verified idempotent webhooks + a reconciliation poller against the Conversation API; restart-safe leased jobs; webhook replay never creates a second quote.
- **Monorepo:** TypeScript + pnpm workspaces (`apps/web`, `apps/control-plane`, `packages/*`). Public HTTPS ingress (deployment or Cloudflare Tunnel/ngrok) so ElevenLabs cloud can reach MCP/webhook routes.
- **Tests:** Vitest unit/contract, MCP/HTTP integration, Playwright E2E, and golden-conversation evals per persona.

## 6. Results & Impact

- **Closed loop demonstrated:** a single vertical runs end to end - voice + document intake -> confirmed immutable spec -> separate consent -> discovery + benchmark -> multiple scheduled calls -> negotiation -> ranked, evidence-backed recommendation.
- **Live negotiation with measurable movement:** at least one session shows `final_total < initial_total` (or measurably improved terms), with `leverage_source` traced to a real benchmark or a previously saved verified quote.
- **Three distinct negotiation styles** handled live, each producing a structured, comparable, itemized outcome; one session surfaces a hidden fee, another a clean quote, a third uses a real prior quote to push the price down.
- **Trust, proven:** AI disclosure, honesty constraints, and friction handling (hang-ups, refusals, "are you a robot?") demonstrated; a suspicious below-market lowball is shown *not* becoming the recommendation.
- **Evidence-backed report:** ranked table with initial->final delta, itemized fees, binding/deposit/validity, benchmark position, red flags, plus transcript-turn and recording citations for every number.
- **Impact:** turns a task almost nobody completes (calling 5-8 operators for one purchase) into an automated, honest, auditable process for any phone-priced market. It directly attacks the wide price spread and the sight-unseen overrun that hurt buyers across verticals - moving being the most documented example (5.6x spread, 40% overrun). Reproducible from a single seed/reset command; real PSTN stays off by default for legal/product safety, and switching to a new vertical is a config change, not a rewrite.

## What was your most fun moment during the hackathon?

The kickoff was amazing - watching the live stream with people from all over the world, we truly felt like part of a big community. Another favorite moment was near the end, once the core work was done and we were recording our submission materials - it was a great feeling to see everything come together.
