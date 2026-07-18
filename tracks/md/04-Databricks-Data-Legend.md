# 04 · Data Legend

**Databricks Challenge · Building the Trust Layer for Indian Healthcare**
**Powered by Databricks — Data Intelligence Platform**
*In collaboration with MIT Club of Northern California and MIT Club of Germany*

---

## 1. Motivation / Goal to Achieve

In a country of 1.4 billion people, you have the chance to build the AI-powered application layer for the healthcare industry — closing the gap between fragmented facility data and life-saving decisions. This is the moonshot: transform healthcare delivery in India, save real lives today, and help define how billions of people access trusted care in the future.

In India, a postal code often determines a lifespan. Families travel hours to reach a hospital — only to discover the ICU was a claim, not a capability. The oxygen supply, neonatal bed, or trauma surgeon they needed was never there. NGOs and public-health planners do not lack data. They lack evidence they can act on.

You are given 10,000 messy records of healthcare facilities across India — structured location and specialty fields mixed with uneven free-text claims about equipment, procedures, and services. The Virtue Foundation and Databricks for Good have spent months building the reasoning layer. Your job is to ship the product layer — a live Databricks App that turns this chaos into decisions a non-technical planner can trust, defend, and save.

We are moving beyond agents that answer questions. We are building the Trust Layer for Indian healthcare.

**Ambitious Goal:** Your mission is to build a Healthcare Facility Intelligence App on Databricks Free Edition that closes the gap between "this hospital says it has an ICU" and "here is the evidence, here is what we don't know, and here is the decision I'm saving for my team."

---

## 2. Core Requirements

> Choose **ONE** mission track. Nail its minimum workflow end-to-end. You are not expected to build all four.

**The Evidence Engine:** Use the Databricks Data Intelligence Platform to extract structure from 10k messy Indian facility records — free-text descriptions, capability claims, procedure lists, equipment logs, and source URLs. Every important output your app produces must trace back to the facility text that supports it.

**The Trust Scorer:** Since there is no answer key, your app must reason about confidence — not just retrieve keywords. A facility claiming Advanced Surgery with no anesthesiologist listed should not rank the same as one with corroborating evidence across three fields. Build logic that flags suspicious or incomplete data and communicates uncertainty honestly.

**The Planner's Workflow:** Ship a Databricks App with a clear, non-technical user journey. Your app must persist user actions — notes, overrides, shortlists, scenarios, or review decisions — so work survives beyond a single session. Demo it live on Free Edition.

### Pick Your Mission

| Track | The Question | Minimum Workflow |
|---|---|---|
| **Facility Trust Desk** | Can this facility actually do what it claims? | Planner selects a capability (ICU, maternity, emergency, oncology, trauma, NICU) and region → sees ranked facilities with trust signals → expands any facility to inspect citations → overrides the assessment with a note. |
| **Medical Desert Planner** | Where are the highest-risk gaps — and how confident are we that they are real? | Planner selects a capability and geography (state, city, district, or PIN) → sees trust-weighted regional coverage → drills into the facility records behind an aggregate → saves a planning scenario. |
| **Referral Copilot** | Where should a patient or coordinator actually go? | User enters a location and care need (e.g., "dialysis near Jaipur" or "emergency surgery near Patna") → receives an evidence-attached shortlist → each candidate shows distance, matching evidence, and gaps → user saves to a shortlist. |
| **Data Readiness Desk** | What must be fixed before this dataset can be trusted for planning? | App surfaces completeness gaps, contradictions, suspicious claims, and high-leverage records → provides a flagged review queue → persists reviewer decisions for downstream use. |

*In this context, "high-leverage" means records where reviewing or correcting them produces a disproportionately large improvement in the overall quality and usefulness of the dataset.*

---

## 3. Stretch Goals

We know that you can do it!

1. **Agentic Traceability:** Go beyond row-level citations. Show the exact sentence and the reasoning step that produced each trust signal. If your app recommends a facility, prove why — extraction → scoring → ranking, with receipts at every step.
   *Hint: Use MLflow 3 Tracing to visualize the thought process behind your evidence engine.*
2. **Self-Correction Loops:** Implement a Validator step that cross-references extracted claims against known medical standards or internal consistency rules — so your primary logic is not hallucinating capabilities that do not exist.
3. **Dynamic Crisis Mapping:** Create a visual dashboard that overlays trust-weighted findings onto a map of India. Highlight the highest-risk medical deserts by Postal Index Number (PIN code) — and visually separate "no hospitals here" from "we don't know what's here." *Inspiration: VF Match Explorer.*
4. **Real-Impact Bonus:** The Databricks for Good team is actively working on these open questions. If your app robustly solves any question marked "could have" or "won't have," call it out in your demo — we want to hear from you.

---

## 4. Areas of Research

Key Questions: The Databricks for Good team is working on these questions. If you can robustly solve questions marked as "could have" or "won't have," please let us know!

**Confidence Scoring:** Real-world data is messy — we are certain this dataset is incomplete and contains errors. How do you quantify trust when there is no ground truth? Can statistics-based methods create prediction intervals around your conclusions so planners know what is solid vs. speculative?

**Claims vs. Evidence:** Fields like capability, procedure, and equipment are claims to verify, not facts. What separates a facility whose description corroborates its ICU claim from one that lists ICU with no supporting text anywhere?

**The Data Desert Problem:** When only 25% of records include capacity and 36% include doctor counts, how does your app prevent a sparse region from looking like a medical desert — when it might just be a data desert?

---

## 5. Hints and Resources

**Infrastructure Requirement & Environment:** This challenge is optimized for Databricks Free Edition. Build and test locally when it helps, then deploy early and demo on Free Edition. Do not use an enterprise or paid organizational workspace for your submission.

**Primary Tech Stack**
- **App Surface:** Databricks Apps — your submission must ship as a live, deployable app.
- **Data Intelligence:** Agent Bricks for Foundation Model Training and Serving.
- **Agentic Engineering:** Genie for autonomous, multi-step data tasks.
- **Observability:** MLflow 3 for agent observability and trace cost tracking.
- **Vector DB:** Mosaic AI Vector Search for high-speed retrieval across 10k rows.
- **Persistence:** Lakebase for user notes, overrides, shortlists, and scenarios.

### Datasets

**The India 10k Dataset:** 10,000 medical facilities across India — structured metadata and deep unstructured notes across 51 columns. Treat extracted evidence fields as noisy claims, not ground truth:

| Field | Coverage |
|---|---|
| description | 100% |
| capability | 99.7% |
| procedure | 92.5% |
| equipment | 77.0% |
| numberDoctors | 36.4% |
| capacity | 25.2% |
| yearEstablished | 47.8% |

Link to dataset — Please create a Databricks account to access the dataset: Login and access the dataset here.
**Virtue Foundation Schema:** Schema Documentation.
**Starter materials:** Prompts and pydantic models used to create the data.

**Submission:** Submit a Git repo and a live Databricks App. Be prepared to give a one-minute demo explaining the user, workflow, technical approach, and key tradeoffs.

---

## 6. Evaluation Criteria

- **Evidence and Trust (35%):** Are outputs grounded in row-level citations? Does the app communicate uncertainty honestly — distinguishing strong evidence from weak claims and data deserts from medical deserts? Since there is no ground truth, we value apps that double-check their own work.
- **Product Judgment (30%):** Is the user clear? Is the workflow intuitive for a non-technical NGO planner? Does the app solve a real decision problem — not just showcase technology behind a chat box?
- **Technical Execution (25%):** Does the app work reliably in a live demo on Free Edition? Are Databricks capabilities — Apps, serverless compute, Vector Search, Lakebase — used well?
- **Ambition (10%):** Did the team go beyond the minimum workflow for their track in a meaningful way — multi-track integration, self-correction loops, crisis mapping, or real-impact alignment?

---

## 7. Why It Matters

In a country of 1.4 billion people, "probably has an ICU" is not good enough. A wrong referral is not a failed query — it is a family that drove six hours for nothing.

By building this trust layer on Databricks, you are creating the product surface that turns 10,000 messy facility records into decisions planners can defend. You are turning a static spreadsheet into a living intelligence network — one that shows its receipts, admits what it doesn't know, and remembers what humans learned along the way.

That is how data becomes action. That is how coordination becomes care.

---
*Hack-Nation × MIT Club of Northern California × MIT Club of Germany · 6th Global AI Hackathon*
