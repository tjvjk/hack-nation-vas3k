---
theme: default
title: The Negotiator — HackNation pitch
info: |
  ## The Negotiator
  Voice agents that call, compare, and negotiate.
author: HackNation team
drawings:
  persist: false
transition: fade
mdc: true
fonts:
  sans: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
---

<style>
:root { --ink:#000; --muted:#000; --orange:#000; --orange-soft:#fff1e5; --green:#000; --green-soft:#e9f8ef; --red:#000; --red-soft:#fff0ed; --line:#dce2ea; --night:#fff; }
.slidev-layout { color:var(--ink); background:#fbfcfe; font-size:20px; }
h1 { font-size:3.1rem; line-height:.98; letter-spacing:-.065em; margin:0; }
h2 { font-size:2.25rem; letter-spacing:-.052em; margin:0 0 .5rem; }
h3 { font-size:1.05rem; margin:0; letter-spacing:-.02em; }
p { line-height:1.35; }
.eyebrow { color:var(--orange); font-size:.68rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin-bottom:1rem; }
.lede { color:var(--muted); font-size:1.12rem; max-width:800px; }
.accent { color:var(--orange); }
.grid { display:grid; gap:16px; }
.grid-2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.grid-3 { grid-template-columns:repeat(3,minmax(0,1fr)); }
.card { background:white; border:1px solid var(--line); border-radius:18px; padding:18px 20px; box-shadow:0 10px 25px rgba(16,24,39,.045); }
.metric { font-weight:850; font-size:2.8rem; line-height:1; letter-spacing:-.07em; color:var(--orange); }
.label { color:var(--muted); font-size:.76rem; line-height:1.3; margin-top:8px; }
.tag { display:inline-block; border-radius:999px; padding:5px 10px; font-size:.68rem; font-weight:750; background:var(--orange-soft); color:#000; }
.status { display:inline-block; border-radius:999px; padding:4px 8px; font-size:.62rem; font-weight:800; color:#000; }
.ok { background:var(--green-soft); }.no { background:var(--red-soft); }.wait { background:#fff4d8; }
.quote { font-size:1.45rem; line-height:1.2; letter-spacing:-.04em; font-weight:720; }
.flow { display:flex; align-items:stretch; gap:8px; margin-top:24px; }
.node { flex:1; border-radius:15px; padding:14px; background:white; border:1px solid var(--line); font-size:.8rem; }
.node b { display:block; margin-bottom:6px; font-size:.9rem; }.arrow { align-self:center; color:var(--orange); font-size:1.5rem; }
.table { width:100%; border-collapse:separate; border-spacing:0 7px; font-size:.78rem; }.table th { color:var(--muted); text-align:left; font-size:.64rem; text-transform:uppercase; letter-spacing:.08em; padding:0 10px 3px; }.table td { padding:11px 10px; background:white; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }.table td:first-child { border-left:1px solid var(--line); border-radius:10px 0 0 10px; }.table td:last-child { border-right:1px solid var(--line); border-radius:0 10px 10px 0; }
.callout { border-left:5px solid var(--orange); background:var(--orange-soft); border-radius:0 16px 16px 0; padding:16px 20px; }
.dark .slidev-layout { color:#000; background:var(--night); }.dark .lede,.dark .label { color:#000; }.dark .card,.dark .node { color:#000; }.dark .eyebrow { color:#000; }
.small { font-size:.76rem; }.tiny { font-size:.62rem; color:var(--muted); }.right { text-align:right; }.bottom { position:absolute; bottom:42px; left:56px; right:56px; }.top-space { margin-top:20px; }
</style>

---
layout: center
class: dark
---

<div class="eyebrow">HackNation · ElevenLabs track</div>

<div class="tag" style="margin-bottom:18px">LLM Plumbers</div>

# The <span class="accent">Negotiator</span>

<p class="lede" style="max-width:640px; margin-top:20px">Voice agents that call, compare, and negotiate — so people stop overpaying in markets where the real price lives on the phone.</p>

<div style="margin-top:34px; display:flex; gap:12px; align-items:center"><span class="tag">Moving · live demo</span><span style="font-size:.8rem">Rock Hill → Charlotte · 45 miles</span></div>

<div class="bottom tiny">Pitch: 3 minutes · Working end-to-end flow · Backup video ready before submission</div>

<!--
0:00–0:08. Hook with the title, then say: “The price of a move should not depend on who has time to make eight phone calls.”
Do not explain the tech yet.
-->

---
layout: default
---

<div class="eyebrow">The problem</div>

# One move. One job. <span class="accent">5.6×</span> different prices.

<p class="lede">Daniel needs to move a two-bedroom apartment 45 miles. To find a fair price, he must repeat the same story to 5–8 companies, decode fees, and negotiate — while his moving date gets closer.</p>

<div class="grid grid-3 top-space">
  <div class="card"><div class="metric">$1,158</div><div class="label">lowest observed quote</div></div>
  <div class="card"><div class="metric">$6,506</div><div class="label">highest observed quote for the same move</div></div>
  <div class="card"><div class="metric">40%</div><div class="label">more likely to exceed the initial estimate when quoted sight-unseen</div></div>
</div>

<div class="callout top-space"><b>People do not lack information.</b> They lack the time and stamina to extract it — one phone call at a time.</div>

<!--
0:08–0:28. Lead with Daniel, not the market size. Pause on “5.6×.”
Source context: project challenge brief; FMCSA statistic is cited in the challenge materials.
-->

---
layout: default
---

<div class="eyebrow">One-sentence solution</div>

# We help <span class="accent">buyers facing phone-priced purchases</span> find a fair deal by sending honest voice agents to call, compare, and negotiate for them.

<div class="flow">
  <div class="node"><b>1 · Intake</b>Voice or document → one confirmed job spec</div><div class="arrow">→</div>
  <div class="node"><b>2 · Call</b>Same spec reaches multiple providers</div><div class="arrow">→</div>
  <div class="node"><b>3 · Negotiate</b>Only real benchmarks and verified quotes</div><div class="arrow">→</div>
  <div class="node"><b>4 · Recommend</b>Comparable, ranked, evidence-backed result</div>
</div>

<div class="grid grid-2 top-space">
  <div class="card"><span class="tag">For the buyer</span><p class="quote" style="margin-top:12px">A fair choice without doing the exhausting work of comparison shopping.</p></div>
  <div class="card"><span class="tag">For the market</span><p class="quote" style="margin-top:12px">A reusable system for moving, auto repair, medical bills, contractors, freight, and more.</p></div>
</div>

<!--
0:28–0:40. Read the first sentence almost verbatim. This is the frame judges should retain.
-->

---
layout: default
---

<div class="eyebrow">Live working demo</div>

# The result is not a chatbot answer. It is a <span class="accent">completed negotiation loop.</span>

<table class="table top-space">
  <thead><tr><th>Carrier</th><th>What happened on the call</th><th>Structured outcome</th><th>Evidence</th></tr></thead>
  <tbody>
    <tr><td><b>Carolina Swift</b><br><span class="tiny">Tough negotiator</span></td><td>$2,950 → <b>$2,780</b><br><span class="tiny">Market benchmark used honestly</span></td><td><span class="status ok">ITEMIZED QUOTE</span></td><td>Call result + itemized terms</td></tr>
    <tr><td><b>Queen City</b><br><span class="tiny">Stonewaller</span></td><td>Will not quote by phone<br><span class="tiny">Agent does not invent a number</span></td><td><span class="status no">DOCUMENTED DECLINE</span></td><td>Terminal outcome recorded</td></tr>
    <tr><td><b>Palmetto Moving</b><br><span class="tiny">Cooperative dispatcher</span></td><td>$2,400 → <b>$2,250</b><br><span class="tiny">Verified prior quote used as leverage</span></td><td><span class="status ok">ITEMIZED QUOTE</span></td><td>Leverage source is traceable</td></tr>
  </tbody>
</table>

<div class="callout top-space"><b>Live demo cue:</b> show the carrier card changing state immediately after the call — no refresh, no manual data entry.</div>

<!--
0:40–1:35. This is the core demo slide, but switch to the app for the actual calls.
Show 10–15 seconds each: successful market-range negotiation; honest decline; verified quote lowers final price.
Keep the dashboard/progress tab visible. Use the recorded 3-minute demo if live audio/network fails.
-->

---
layout: default
---

<div class="eyebrow">What makes the outcome trustworthy</div>

# Negotiation is useful only if the <span class="accent">facts stay honest.</span>

<div class="grid grid-2 top-space">
  <div class="card"><h3>One immutable specification</h3><p class="small" style="margin-top:8px">Every carrier receives the same confirmed route, inventory, date, and service needs — making quotes comparable by construction.</p></div>
  <div class="card"><h3>Real leverage, never a fake bid</h3><p class="small" style="margin-top:8px">The agent can cite a market benchmark or a previously verified quote — not invented urgency or inventory.</p></div>
  <div class="card"><h3>Separate outreach consent</h3><p class="small" style="margin-top:8px">No call campaign starts until the buyer grants explicit, scoped consent.</p></div>
  <div class="card"><h3>Lowball ≠ winner</h3><p class="small" style="margin-top:8px">Suspiciously below-market quotes are flagged for review, not automatically recommended.</p></div>
</div>

<div class="top-space" style="display:flex; gap:10px; align-items:center"><span class="status ok">AI DISCLOSURE</span><span class="status ok">TRANSCRIPT / RECORDING</span><span class="status ok">TERMINAL STATES</span><span class="status ok">AUDITABLE RANKING</span></div>

<!--
1:35–1:55. This replaces vague “responsible AI” claims with concrete product behavior.
Use the documented decline as proof: handling “no” correctly is part of trust.
-->

---
layout: default
---

<div class="eyebrow">The product architecture</div>

# High-level by design: <span class="accent">voice in, verified outcome out.</span>

<div class="flow" style="margin-top:30px">
  <div class="node"><b>Estimator agent</b>Voice / document intake<br><span class="tiny">confirmed MoveSpec</span></div><div class="arrow">→</div>
  <div class="node"><b>Control plane</b>Consent · carrier campaign · benchmark · call scope</div><div class="arrow">→</div>
  <div class="node"><b>Negotiator agent</b>Browser voice session<br><span class="tiny">carrier-specific, scoped context</span></div><div class="arrow">→</div>
  <div class="node"><b>Report</b>Ranked quotes · flags · transcript / recording links</div>
</div>

<div class="grid grid-3 top-space">
 <div class="card"><h3>Safety boundary</h3><p class="small" style="margin-top:8px">Server-side call permissions prevent agents from exceeding their role or campaign scope.</p></div>
 <div class="card"><h3>Reliable state</h3><p class="small" style="margin-top:8px">Each call closes in a structured terminal result; webhooks are verified and idempotent.</p></div>
 <div class="card"><h3>Demo-safe delivery</h3><p class="small" style="margin-top:8px">Human-in-the-loop browser carrier console today; real outbound calling remains off by default.</p></div>
</div>

<!--
1:55–2:10. Do not show code, SDK names, or file trees. This answers “how is it real?” in one diagram.
-->

---
layout: default
---

<div class="eyebrow">Beyond moving</div>

# The call pattern stays the same. <span class="accent">The market configuration changes.</span>

<div class="grid grid-2 top-space">
 <div class="card"><span class="tag">Moving today</span><h3 style="margin-top:13px">Route · rooms · stairs · inventory</h3><p class="small" style="margin-top:10px">Benchmark: moving-cost range. Red flags: sight-unseen lowball and hidden fees.</p></div>
 <div class="card"><span class="tag">Auto repair next</span><h3 style="margin-top:13px">Vehicle · symptom · mileage · parts</h3><p class="small" style="margin-top:10px">Benchmark: regional repair range. Same call, comparison, consent, and evidence flow.</p></div>
</div>

<div class="grid grid-3 top-space">
  <div class="card"><h3>Medical bills</h3><p class="small" style="margin-top:8px">Negotiate balances and payment plans.</p></div>
  <div class="card"><h3>Contractor bids</h3><p class="small" style="margin-top:8px">Normalize scope and compare exclusions.</p></div>
  <div class="card"><h3>Freight & rentals</h3><p class="small" style="margin-top:8px">Make opaque phone quotes legible.</p></div>
</div>

<!--
2:10–2:25. Use the short bonus video clip only if timing permits. Say “same workflow, different taxonomy,” not “we solved every vertical.”
-->

---
layout: center
class: dark
---

<div class="eyebrow">Impact</div>

# The fair price already exists.<br>We make it <span class="accent">reachable.</span>

<p class="lede" style="margin-top:22px">The Negotiator turns a task that almost nobody completes — calling, comparing, and haggling across fragmented businesses — into an honest, auditable decision.</p>

<div style="display:flex; gap:12px; margin-top:32px"><span class="tag">More time for people</span><span class="tag">More evidence in every decision</span><span class="tag">One reusable platform</span></div>

<div class="bottom" style="display:flex; justify-content:space-between; font-size:.68rem"><span>Demo tabs: intake · campaign · carrier console · final report</span><span>Fallback: pre-recorded demo video</span></div>

<!--
2:25–3:00. Close with impact, not a feature list. End with: “The Negotiator makes the fair price reachable.”
Before pitching: open the four tabs in the footer, start each browser session, and keep the recorded demo locally available.
-->
