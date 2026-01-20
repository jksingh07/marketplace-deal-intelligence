# Repo Structure — AI Pipeline (Stages 4–9)

This repo implements the AI/ML pipeline that runs AFTER scraping.
Scraping produces raw listing JSON + raw HTML + image URLs.
AI pipeline consumes those and produces structured intelligence + recommendations.

## Recommended Folder Layout

.
├── docs/
│   ├── AI_PIPELINE_OVERVIEW.md
│   ├── REPO_STRUCTURE_AI.md
│   ├── STAGE_4_IMPLEMENTATION.md
│   └── STAGE_OUTPUT_CONTRACTS.md
│
├── contracts/
│   ├── stage4_description_intel.schema.json
│   ├── stage7_price_intel.schema.json
│   ├── stage8_alternatives.schema.json
│   ├── stage9_buyer_summary.schema.json
│   └── VERSION.md
│
├── stages/
│   ├── stage4_description_intel/
│   │   ├── README.md
│   │   ├── rules/
│   │   │   ├── high_risk_terms.md
│   │   │   └── patterns.md
│   │   ├── prompts/
│   │   │   ├── extractor_prompt.md
│   │   │   └── question_generator_prompt.md
│   │   ├── eval/
│   │   │   ├── labeled_set.md
│   │   │   └── eval_criteria.md
│   │   └── outputs/
│   │       └── examples.md
│   │
│   ├── stage7_price_intel/
│   ├── stage8_alternatives/
│   └── stage9_buyer_summary/
│
├── common/
│   ├── schema_validation.md
│   ├── idempotency.md
│   ├── evidence_format.md
│   ├── comparable_retrieval.md
│   └── scoring_guidelines.md
│
├── data_samples/
│   ├── raw_listing_examples/
│   └── stage_outputs_examples/
│
└── README.md


## Why This Layout

- docs/ explains the system for humans + Cursor
- contracts/ prevents silent breaking changes between stages
- stages/ keeps each stage isolated and replayable
- common/ holds shared concepts (retrieval, idempotency, evidence formats)
- data_samples/ makes testing and prompt iteration easy


## Golden Rules For Every Stage

1. Each stage is **pure**:
   Input = listing snapshot + prior stage outputs
   Output = new stage record with version metadata

2. Outputs are **idempotent**:
   Running the same stage twice with the same snapshot should produce the same record.

3. Every extracted signal must carry:
   - evidence text span
   - confidence

4. LLMs can:
   - extract structured fields
   - explain outputs
   - generate questions
   LLMs cannot:
   - invent facts
   - override deterministic computations