# AI Pipeline Overview — Marketplace Deal Intelligence

## Purpose (Why this exists)

This project builds an **AI-powered deal intelligence system** on top of Facebook Marketplace listings (vehicles & bikes).

The goal is to turn messy, misleading, and incomplete listings into:
- clear risk analysis
- fair price estimates
- better alternative recommendations
- buyer-ready summaries with negotiation help

Scraping already exists.  
This document explains **what the AI/ML system is building on top of that data**.

---

## Core Design Principles (Non-Negotiable)

1. **Scraping ≠ Processing**
   - Scrapers only collect raw data
   - No AI, no parsing, no scoring during scraping

2. **Raw data is immutable**
   - Raw listing snapshots are never modified
   - All AI outputs are derived and re-computable

3. **Step-based processing**
   - Each AI stage is independent
   - Each stage has a clear input/output contract
   - Stages can be re-run safely

4. **Explainability over magic**
   - LLMs extract and explain
   - Scores are computed, not hallucinated

---

## High-Level Pipeline (AI-Owned Stages)

The AI/ML pipeline starts **after scraping** and covers **Stage 4 → Stage 9**.

Raw Listing JSON
↓
Stage 4 — Description Intelligence
↓
Stage 7 — Price & Deal Intelligence
↓
Stage 8 — Alternative Recommender
↓
Stage 9 — Buyer-Ready Summary
↓
(Added later)
Stage 6 — Seller Profile Intelligence
Stage 5 — Image Analysis


---
## Stage 4 — Description Intelligence (FOUNDATION)

### Goal
Convert unstructured listing text into **structured, explainable intelligence**
using an **LLM-first extraction pipeline with deterministic guardrails**.

### Core Approach
- LLM is the **primary extractor** for issues, mods, risks, and seller intent.
- A small ruleset acts as a **safety net** for explicit high-severity terms.
- All extracted signals must include **verbatim evidence** from the text.
- Signals are classified as:
  - **Verified** (explicit evidence)
  - **Inferred** (implicit or soft language)

### What This Stage Produces
- structured condition & risk signals
- maintenance and modification intelligence
- seller intent and negotiation stance
- missing critical information
- buyer follow-up questions
- confidence and evidence for every signal

### Why This Matters
This design ensures:
- high recall from natural language understanding
- near-zero miss rate on catastrophic risks
- consistent, replayable outputs
- downstream stages never rely on hallucinated facts

Stage 4 is the **single most important dependency** for pricing,
alternatives, and buyer-facing recommendations.
---

## Stage 7 — Price & Deal Intelligence

### Goal
Estimate **fair market value** and determine if a listing is:
- underpriced
- fairly priced
- overpriced

### Inputs
- normalized listing attributes
- Stage 4 outputs
- comparable listings from the database

### Outputs
- estimated market price (p25 / p50 / p75)
- deal delta (asking vs market)
- deal rating
- explanation of adjustments
- confidence score

### Notes
- Uses robust statistics (not single-point estimates)
- Market value is based on observed marketplace data
- Must always return a range, not a single number

---

## Stage 8 — Alternative Recommender

### Goal
Show **better or similar options** so buyers don’t regret their decision.

### Inputs
- current listing
- Stage 7 pricing output
- comparable listing pool

### Outputs
- list of alternative listings
- why each alternative is better
- relative value scores

### Retrieval Strategy
1. Hard filters (make, model, year band, location)
2. Ranking based on:
   - price advantage
   - mileage
   - risk flags
   - (later) seller trust

---

## Stage 9 — Buyer-Ready Summary (USER OUTPUT)

### Goal
Turn all structured AI outputs into a **clear, helpful buyer-facing summary**.

### Inputs
- Stage 4 (description intel)
- Stage 7 (price intel)
- Stage 8 (alternatives)

### Outputs
- overall verdict
- key pros & cons
- follow-up questions to ask seller
- negotiation suggestions
- recommended actions
- known unknowns
- confidence level

### Notes
- LLM generates text **only from structured fields**
- No raw HTML or guessing allowed
- Must remain consistent with computed numbers

---

## Stage 6 — Seller Profile Intelligence (Post-MVP)

### Goal
Assess how trustworthy a seller is.

### Signals
- account age
- rating & rating count
- rating distribution
- active listings count
- behavioral risk signals

### Output
- seller trust score (smoothed, not naive)
- seller risk flags

Used to:
- adjust confidence
- influence alternatives ranking
- inform negotiation tone

---

## Stage 5 — Image Analysis (LAST STAGE)

### Goal
Extract visual risk and quality signals from listing images.

### MVP Focus
- photo quality score
- photo coverage (interior, exterior, engine, odometer)
- obvious damage flags
- contradictions with description claims

### Notes
- No insurance-grade damage claims
- Outputs are probabilistic & conservative
- Enhances confidence, doesn’t dominate decisions

---

## Key Metrics (Computed, Not Prompted)

### Flipability Score
How easy it is to buy and resell for profit.

Factors:
- undervaluation vs market
- liquidity of model
- risk penalties
- seller trust (later)

### Fit Score
How well the listing matches a user’s preferences.

Factors:
- budget
- mileage tolerance
- year range
- risk tolerance
- location

---

## MVP Build Order (Strict)

1. Stage 4 — Description Intelligence
2. Stage 7 — Price & Deal Intelligence
3. Stage 8 — Alternative Recommender
4. Stage 9 — Buyer-Ready Summary
5. Stage 6 — Seller Trust
6. Stage 5 — Image Analysis

Do **not** change this order.

---

## Final Note (For Future Developers & LLMs)

This system is designed to:
- be explainable
- be replayable
- evolve as models improve
- avoid hard coupling between stages

If you are adding logic:
- define the schema first
- make outputs deterministic where possible
- keep raw data untouched