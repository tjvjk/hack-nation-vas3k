---
theme: default
title: "The Negotiator — LLM Plumbers"
info: |
  HackNation / ElevenLabs
  LLM Plumbers — The Negotiator
drawings:
  persist: false
transition: slide-left
mdc: true
layout: cover
class: text-left deck-white
---

# Let's voice agents<br>works for you

<br>

**LLM Plumbers · The Negotiator**

<div class="problem-note">
For one identical 45-mile move, Daniel saw prices from <b>$1,158</b> to <b>$6,506</b>.<br>
The only way to find a fair price is to call 5–8 movers, repeat the same story, compare hidden fees, and negotiate.
</div>

<!--
0:00–0:20 — Open with Daniel, not the product. “The price of a move should not depend on who has the time to make eight calls.”
-->

<style>
:root { --ink: #000; --paper: #fff; --line: #d9d9d9; --blue: #dcecff; --purple: #eee3ff; --orange: #fff0d7; --green: #e3f5e9; --pink: #ffe4ed; }
.slidev-layout { color: var(--ink); background: var(--paper); font-size: 1.08em; }
.slidev-layout h1, .slidev-layout h2, .slidev-layout h3, .slidev-layout p, .slidev-layout li, .slidev-layout td, .slidev-layout th, .slidev-layout a { color: #000 !important; }
.slidev-layout h1 { font-size: 2.05em; line-height: 1.14; letter-spacing: -.035em; }
.slidev-layout h2 { letter-spacing: -.025em; }
.deck-white { background: #fff !important; }
.problem-note { margin-top: 2rem; max-width: 850px; border-left: 7px solid #000; padding: .6rem 0 .6rem 1rem; font-size: .8em; line-height: 1.45; }
.deck-kicker { font-size: .58em; font-weight: 800; text-transform: uppercase; letter-spacing: .16em; margin-bottom: .6rem; }
.big-line { font-size: 1.42em; line-height: 1.25; font-weight: 700; max-width: 850px; }
.caption { font-size: .58em; line-height: 1.35; }
.pill { display: inline-block; border: 1.5px solid #000; border-radius: 999px; padding: .24rem .6rem; font-size: .54em; font-weight: 700; margin: .12rem; }
.simple-list { margin: 1.2rem 0 0 1.2rem; font-size: .78em; line-height: 1.65; }
.simple-list li { padding-left: .25rem; }
.callout { border: 2px solid #000; border-radius: 14px; padding: .8rem 1rem; font-size: .73em; line-height: 1.35; }
.soft-blue { background: var(--blue); }.soft-purple { background: var(--purple); }.soft-orange { background: var(--orange); }.soft-green { background: var(--green); }.soft-pink { background: var(--pink); }
.flow { display: grid; grid-template-columns: repeat(4, 1fr); align-items: stretch; gap: .55rem; margin-top: 1.4rem; }
.flow > div { border: 2px solid #000; border-radius: 14px; padding: .7rem; font-size: .65em; line-height: 1.25; }.flow b { display: block; font-size: 1.14em; margin-bottom: .4rem; }
.arrow { display: flex; align-items: center; justify-content: center; font-size: 1.3em; font-weight: 700; }
.demo-grid { display: grid; grid-template-columns: 1fr 1.1fr; gap: 1.1rem; align-items: center; }
.demo-card { border: 2px solid #000; border-radius: 18px; padding: 1.1rem; }.demo-card p { margin: .25rem 0; font-size: .66em; }.demo-step { display: flex; gap: .65rem; align-items: baseline; margin: .5rem 0; }.demo-step b { font-size: .85em; }
.team-photo { width: 100%; height: 440px; object-fit: cover; object-position: 50% 42%; border: 2px solid #000; border-radius: 16px; display:block; }
.github-links { margin-top: 1.2rem; font-size: .62em; line-height: 1.65; }.github-links a { text-decoration: underline; }
.video-wrap { width: 100%; height: 430px; border: 2px solid #000; border-radius: 16px; overflow: hidden; background: #000; }.video-wrap video { width: 100%; height: 100%; object-fit: contain; display:block; }
.approaches { display:grid; grid-template-columns: repeat(3, 1fr); gap: .8rem; margin-top: 1.1rem; }.approaches > div { border: 2px solid #000; border-radius: 16px; padding: .85rem; min-height: 215px; }.approaches h3 { margin: .3rem 0 .55rem; font-size: .78em; }.approaches p { margin:0; font-size: .61em; line-height: 1.4; }
.architecture { display:grid; grid-template-columns: 1fr .25fr 1fr .25fr 1fr .25fr 1fr; align-items:center; gap:.25rem; margin-top:1.5rem; }.architecture .box { border:2px solid #000; border-radius:16px; padding:.8rem; min-height:155px; font-size:.62em; line-height:1.35; }.architecture b { display:block; font-size:1.15em; margin-bottom:.4rem; }.architecture .arr { font-size:1.4em; text-align:center; }
.mentor-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:1.25rem; align-items:end; margin-top:1rem; }.mentor { text-align:center; }.mentor img { height:265px; max-width:100%; object-fit:contain; display:block; margin:auto; }.mentor b { display:block; margin-top:.25rem; }.qr-grid { display:grid; grid-template-columns:repeat(2, 1fr); gap:3rem; max-width:800px; margin:1.25rem auto 0; text-align:center; }.qr-grid img { width:205px; height:205px; image-rendering:auto; border:1px solid #000; }.qr-grid a { display:block; font-size:.61em; margin-top:.35rem; text-decoration:underline; }
</style>

---
layout: center
class: deck-white
---

## The Problem

<div class="big-line" style="margin-top:1.2rem">Moving is hard. You need to call many companies, explain the same move again and again, and compare their prices.</div>

<ul class="simple-list">
  <li>Many phone calls</li>
  <li>The same details again and again</li>
  <li>Extra fees that are hard to see</li>
  <li>Prices that are hard to compare</li>
</ul>

## Solution: Burn tokens<br>instead of spending your time.

<p class="caption" style="margin-top:2rem; max-width:760px">An AI agent can make these calls, collect the important details, and ask for a better price. You can spend your time on packing and your new home.</p>

<!--
0:20–0:30 — One beat of humor. Do not overexplain tokens. Pivot immediately to what agents do better.
-->

---
layout: default
class: deck-white
---

<div class="deck-kicker">The Negotiator</div>

# One confirmed job. Multiple honest calls. One decision.

<div class="flow">
  <div class="soft-blue"><b>1. Tell us once</b><br/>Voice interview or document / form submission creates a single, confirmed move spec.</div>
  <div class="soft-purple"><b>2. Call for you</b><br/>The agent reaches movers with the exact same facts and explicit consent.</div>
  <div class="soft-orange"><b>3. Negotiate honestly</b><br/>It uses only a real benchmark or a verified competing quote.</div>
  <div class="soft-green"><b>4. Pick with proof</b><br/>Ranked prices, itemized terms, red flags, transcripts, and recordings.</div>
</div>

<div class="callout soft-pink" style="margin-top:1.2rem"><b>We help people facing phone-priced purchases get a fair deal</b> by sending voice agents to call, compare, and negotiate for them.</div>

<!--
0:30–0:45 — Solution overview. The system is not “a chatbot that recommends”; it completes the tedious loop.
-->

---
layout: two-cols
class: deck-white
---

# Our Team: LLM Plumbers

<p style="font-size:.72em; max-width:520px">Three people who were tired of plumbing opaque workflows by hand — so we built agents that pick up the phone.</p>

<div class="callout soft-blue" style="margin-top:1.1rem"><b>Built during HackNation</b><br>Product, voice-agent orchestration, backend, and demo — one team, one weekend.</div>

<div style="margin-top:1.1rem; font-size:.75em"><b>LLM Plumbers</b><br><span class="caption">From left to right: Slach · Dmitry · Ramil</span></div>

<div class="github-links">
  <a href="https://github.com/Slach" target="_blank">github.com/Slach</a><br>
  <a href="https://github.com/tjvjk" target="_blank">github.com/tjvjk</a><br>
  <a href="https://github.com/ramilmustafin" target="_blank">github.com/ramilmustafin</a>
</div>

::right::

<div style="padding-top:.4rem"><img class="team-photo" src="./assets/team_photo.jpg" alt="LLM Plumbers team" /></div>

<!--
0:45–0:55 — Name the team quickly. The image crop intentionally centers the three faces and the laptop.
-->

---
layout: default
class: deck-white
---

<div class="deck-kicker">Live working demo</div>

# From one move request to a recommendation

<div class="demo-grid" style="margin-top:1.1rem">
  <div class="demo-card soft-blue">
    <div class="demo-step"><b>01</b><span><b>Intake</b><br><span class="caption">Rock Hill → Charlotte · 45 miles · 2-bedroom apartment</span></span></div>
    <div class="demo-step"><b>02</b><span><b>Consent & campaign</b><br><span class="caption">Three carriers, one immutable spec</span></span></div>
    <div class="demo-step"><b>03</b><span><b>Calls</b><br><span class="caption">Price, terms, and transcript are collected live</span></span></div>
    <div class="demo-step"><b>04</b><span><b>Recommendation</b><br><span class="caption">Comparable quotes + evidence, not a black box</span></span></div>
  </div>
  <div>
    <div class="callout soft-orange"><b>Demo order</b><br><span class="caption">1. A market benchmark moves a high quote.<br>2. A mover refuses to quote — the agent records the decline, it does not bluff.<br>3. A verified quote becomes leverage and reduces the final price.</span></div>
    <div class="callout soft-green" style="margin-top:.7rem"><b>What the jury should watch for</b><br><span class="caption">The campaign card changes to a structured terminal result immediately after every call.</span></div>
  </div>
</div>

<!--
0:55–1:35 — This is the live-demo setup. Switch to the open product tabs: intake, campaign, carrier console, and final report.
The next slide contains the local recorded fallback video.
-->

---
layout: default
class: deck-white
---

<div class="deck-kicker">Recorded demo · fallback for the live flow</div>

# The Negotiator in action

<div class="video-wrap" style="margin-top:.8rem"><video src="/video/demo.mp4" controls preload="metadata" poster="" aria-label="The Negotiator demo video"></video></div>

<p class="caption" style="margin-top:.35rem">52-second recording of the working voice-agent flow. Click play during the pitch if the live session is unavailable.</p>

<!--
1:35–2:27 — Play the video. It is intentionally embedded from presentation/public/video/demo.mp4 so the deck remains self-contained after build.
-->

---
layout: default
class: deck-white
---

<div class="deck-kicker">Three conversation approaches we tested</div>

# Negotiation means adapting — not reading one script.

<div class="approaches">
  <div class="soft-orange"><span class="pill">01 · benchmark</span><h3>Firm price → market reference</h3><p>Carolina Swift opens at <b>$2,950</b>. The agent cites a real market range; the mover reduces the quote to <b>$2,780</b>.</p></div>
  <div class="soft-pink"><span class="pill">02 · honest stop</span><h3>No quote → documented decline</h3><p>Queen City refuses a phone quote. The agent thanks them and records <b>documented_decline</b> — no fabricated price, no fake success.</p></div>
  <div class="soft-green"><span class="pill">03 · verified leverage</span><h3>Prior quote → lower final price</h3><p>Palmetto starts at <b>$2,400</b>. The agent references a verified competing quote, and reaches <b>$2,250</b>.</p></div>
</div>

<!--
2:27–2:42 — These are the three call patterns from the demo script. Emphasize causality: the price changes only after real leverage appears.
-->

---
layout: default
class: deck-white
---

<div class="deck-kicker">How it works</div>

# Voice in. Evidence-backed outcome out.

<div class="architecture">
  <div class="box soft-blue"><b>Estimator agent</b>Voice or document intake creates the confirmed job specification.</div>
  <div class="arr">→</div>
  <div class="box soft-purple"><b>Control plane</b>Consent, benchmark, carrier campaign, and scoped call context.</div>
  <div class="arr">→</div>
  <div class="box soft-orange"><b>Negotiator agent</b>Calls through the browser demo session and saves structured outcomes.</div>
  <div class="arr">→</div>
  <div class="box soft-green"><b>Decision report</b>Ranked quotes, terms, red flags, transcript, and recording links.</div>
</div>

<div class="callout" style="margin-top:1.15rem"><b>Trust is a product feature:</b> same immutable spec for every provider · separate consent before outreach · real leverage only · suspicious lowballs are flagged, never auto-selected.</div>

<!--
2:42–2:55 — High-level diagram only. No code, SDK logos, or file tree.
-->

---
layout: center
class: deck-white
---

# Спасибо mentors!

<div class="mentor-grid">
  <div class="mentor"><img src="./assets/mentor1.png" alt="Vardineh QR code" /><b>Vardineh</b></div>
  <div class="mentor"><img src="./assets/mentor2.png" alt="Wolf QR code" /><b>Wolf</b></div>
  <div class="mentor"><img src="./assets/mentor3.png" alt="Levon QR code" /><b>Levon</b></div>
</div>

<!--
2:55–3:00 — Thank mentors briefly. Then advance to the final QR slide for questions/networking.
-->

---
layout: end
class: deck-white
---

# Try The Negotiator

<div class="qr-grid">
  <div><a href="http://calls.feedfinch.com" target="_blank"><img src="/qrs/product.png" alt="QR code for calls.feedfinch.com" /></a><b style="display:block; margin-top:.35rem">Live product</b><a href="http://calls.feedfinch.com" target="_blank">calls.feedfinch.com</a></div>
  <div><a href="https://github.com/tjvjk/hack-nation-vas3k" target="_blank"><img src="/qrs/repository.png" alt="QR code for GitHub repository" /></a><b style="display:block; margin-top:.35rem">Source code</b><a href="https://github.com/tjvjk/hack-nation-vas3k" target="_blank">github.com/tjvjk/hack-nation-vas3k</a></div>
</div>

<p class="caption" style="margin-top:1rem">LLM Plumbers · The Negotiator · HackNation / ElevenLabs</p>
