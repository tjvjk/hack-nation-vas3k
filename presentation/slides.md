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
.video-wrap { border: 2px solid #000; border-radius: 16px; overflow: hidden; background: #000; }.video-wrap video { width: 100%; height: 100%; object-fit: contain; display:block; }
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

<div class="deck-kicker">Recorded demo · fallback for the live flow</div>

# The Negotiator in action

<div class="video-wrap" style="width:220px!important; height:391px!important; margin:.8rem auto 0!important; overflow:hidden!important"><video src="/video/demo.mp4" controls preload="metadata" poster="" aria-label="The Negotiator demo video"></video></div>

<!--
1:35–2:27 — Play the video. It is intentionally embedded from presentation/public/video/demo.mp4 so the deck remains self-contained after build.
-->

---
layout: center
class: deck-white
---

# Спасибо mentors!

<div class="mentor-grid" style="display:flex!important; width:100%!important; gap:1rem!important; align-items:flex-start!important; justify-content:center!important">
  <div class="mentor" style="flex:1 1 0!important; min-width:0!important"><img style="width:100%!important; height:230px!important; object-fit:contain!important" src="./assets/mentor1.png" alt="Vardineh QR code" /><b>Vardineh</b></div>
  <div class="mentor" style="flex:1 1 0!important; min-width:0!important"><img style="width:100%!important; height:230px!important; object-fit:contain!important" src="./assets/mentor2.png" alt="Wolf QR code" /><b>Wolf</b></div>
  <div class="mentor" style="flex:1 1 0!important; min-width:0!important"><img style="width:100%!important; height:230px!important; object-fit:contain!important" src="./assets/mentor3.png" alt="Levon QR code" /><b>Levon</b></div>
</div>

<!--
2:55–3:00 — Thank mentors briefly. Then advance to the final QR slide for questions/networking.
-->

---
layout: end
class: deck-white
---

# Try The Negotiator

<div class="qr-grid" style="display:flex!important; width:100%!important; max-width:none!important; margin:1.25rem auto 0!important; gap:2.5rem!important; justify-content:center!important">
  <div style="flex:0 0 auto!important; text-align:center!important; white-space:nowrap!important"><a href="http://calls.feedfinch.com" target="_blank" style="display:block!important"><img style="display:block!important; width:180px!important; height:180px!important; margin:0 auto!important" src="/qrs/product.png" alt="QR code for calls.feedfinch.com" /></a><b style="display:block; margin-top:.35rem; white-space:nowrap!important">Live product</b><a href="http://calls.feedfinch.com" target="_blank" style="display:block!important; white-space:nowrap!important">calls.feedfinch.com</a></div>
  <div style="flex:0 0 auto!important; text-align:center!important; white-space:nowrap!important"><a href="https://github.com/tjvjk/hack-nation-vas3k" target="_blank" style="display:block!important"><img style="display:block!important; width:180px!important; height:180px!important; margin:0 auto!important" src="/qrs/repository.png" alt="QR code for GitHub repository" /></a><b style="display:block; margin-top:.35rem; white-space:nowrap!important">Source code</b><a href="https://github.com/tjvjk/hack-nation-vas3k" target="_blank" style="display:block!important; white-space:nowrap!important">github.com/tjvjk/hack-nation-vas3k</a></div>
</div>

<p class="caption" style="margin-top:1rem">LLM Plumbers · The Negotiator · HackNation / ElevenLabs</p>

---
layout: default
class: deck-white
---

<div class="deck-kicker">Live system architecture</div>

# One voice workflow. One control plane.

<div style="display:flex!important; align-items:stretch!important; justify-content:center!important; gap:.45rem!important; margin-top:1.25rem!important">
  <div class="callout soft-purple" style="width:27%!important; margin:0!important; text-align:center!important"><b>ElevenLabs Agents</b><br><span class="caption">Voice reasoning<br>Conversation runtime</span></div>
  <div style="display:flex!important; align-items:center!important; font-size:1.5em!important">↔</div>
  <div class="callout soft-blue" style="width:27%!important; margin:0!important; text-align:center!important"><b>Orchestrator widget</b><br><span class="caption">Browser voice session<br>Carrier demo console</span></div>
  <div style="display:flex!important; align-items:center!important; font-size:1.5em!important">↔</div>
  <div class="callout soft-orange" style="width:27%!important; margin:0!important; text-align:center!important"><b>Orchestrator backend</b><br><span class="caption">REST state · MCP tools<br>Signed URLs · webhooks</span></div>
</div>

<div style="display:flex!important; justify-content:flex-end!important; gap:.6rem!important; margin-top:1rem!important; padding-right:2.5%!important">
  <div style="font-size:1.4em!important; line-height:1!important">↙</div>
  <div style="font-size:1.4em!important; line-height:1!important">↘</div>
</div>

<div style="display:flex!important; justify-content:flex-end!important; gap:.8rem!important">
  <div class="callout soft-green" style="width:27%!important; margin:0!important; text-align:center!important"><b>Google Maps API</b><br><span class="caption">Origin / destination → Place IDs</span></div>
  <div class="callout soft-pink" style="width:27%!important; margin:0!important; text-align:center!important"><b>MovingBuddha API</b><br><span class="caption">Market benchmark range</span></div>
</div>

<p class="caption" style="margin-top:1rem; text-align:center"><b>Data stays server-side:</b> API keys and ElevenLabs credentials never enter the browser.</p>

---
layout: default
class: deck-white
clicks: 3
---

<div class="deck-kicker">Product walkthrough · click to advance</div>

# From intake to a live call

<div style="position:relative!important; height:355px!important; margin-top:.8rem!important; border:2px solid #000!important; border-radius:16px!important; overflow:hidden!important; background:#f7f7f7!important">
  <div v-click="[0, 0]" style="position:absolute!important; inset:0!important; display:flex!important; align-items:center!important; justify-content:center!important; padding:12px!important"><img style="max-width:100%!important; max-height:100%!important; object-fit:contain!important" src="./assets/intake_1.png" alt="Move request intake screen" /></div>
  <div v-click="[1, 1]" style="position:absolute!important; inset:0!important; display:flex!important; align-items:center!important; justify-content:center!important; padding:12px!important"><img style="max-width:100%!important; max-height:100%!important; object-fit:contain!important" src="./assets/extraction_1.png" alt="Extracted move details screen" /></div>
  <div v-click="[2, 2]" style="position:absolute!important; inset:0!important; display:flex!important; align-items:center!important; justify-content:center!important; padding:12px!important"><img style="max-width:100%!important; max-height:100%!important; object-fit:contain!important" src="./assets/answer_1.png" alt="Live carrier call screen" /></div>
</div>

<div style="display:flex!important; justify-content:center!important; gap:.5rem!important; margin-top:.6rem!important; font-size:.63em!important; font-weight:700!important">
  <span v-click="[0, 0]" class="pill">01 · intake</span>
  <span v-click="[1, 1]" class="pill">02 · extraction</span>
  <span v-click="[2, 2]" class="pill">03 · live call</span>
</div>
