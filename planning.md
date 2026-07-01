# Provenance Guard Planning

## Project Overview

Provenance Guard is a backend API that helps creative platforms estimate whether submitted text is likely AI-generated or human-written. Rather than making absolute decisions, the system combines multiple detection signals, produces a confidence score, displays a transparency label, and allows creators to appeal classifications.

---

# Detection Signals

## Signal 1 – LLM-based Detection

The first signal uses Groq's Llama 3.3 model to analyze writing style and estimate the likelihood that a passage was AI-generated.

Output:

- score (0.0 – 1.0)
- explanation

Strengths

- Understands semantic consistency
- Detects repetitive AI writing patterns
- Considers overall writing quality

Limitations

- May mistake polished human writing for AI
- May be inconsistent on very short text

---

## Signal 2 – Stylometric Analysis

The second signal computes measurable writing characteristics.

Metrics include:

- Sentence length variance
- Type-token ratio
- Average sentence length
- Word count
- Punctuation density

Output:

- score (0.0 – 1.0)
- metrics dictionary

Strengths

- Fast
- Deterministic
- Explainable

Limitations

- Poems
- Technical papers
- Non-native English writers

---

# Confidence Scoring

The final confidence score combines both signals.

Weighting

- LLM score: 60%
- Stylometric score: 40%

Confidence ranges

| Score | Classification |
|-------|----------------|
| 0.00 – 0.39 | Likely Human |
| 0.40 – 0.69 | Uncertain |
| 0.70 – 1.00 | Likely AI |

This conservative design helps reduce false positives by requiring stronger evidence before labeling content as AI-generated.

---

# Transparency Labels

## High-confidence AI

> This content is likely AI-generated based on multiple detection signals. Readers should interpret it accordingly.

## High-confidence Human

> This content is likely written by a human author. No significant AI indicators were detected.

## Uncertain

> The system could not confidently determine whether this content was human-written or AI-generated. Readers should treat the attribution as uncertain, and the creator may provide additional context.

---

# Appeals Workflow

Creators may appeal any classification.

The appeal contains:

- content_id
- creator_reasoning

After submission:

- status becomes "under_review"
- appeal_reasoning is stored
- audit log is updated
- human reviewer may inspect later

---

# Edge Cases

Potential difficult cases include:

- Poetry with repetitive language
- Academic writing
- ESL (non-native English) writers
- AI text heavily edited by humans
- Very short submissions

---

# Architecture

                    POST /submit
                          │
                          ▼
                LLM Detection Signal
                          │
                          ▼
            Stylometric Detection Signal
                          │
                          ▼
              Confidence Score Combiner
                          │
                          ▼
               Transparency Label Engine
                    │              │
                    ▼              ▼
              Audit Log      JSON Response


                    POST /appeal
                          │
                          ▼
                Update Submission Status
                          │
                          ▼
                     Audit Log

Submission Flow:

A user submits text through `/submit`. The system evaluates the content using both the LLM detector and stylometric analysis, combines the results into a confidence score, generates a transparency label, records the decision in the audit log, and returns the response.

Appeal Flow:

A creator submits an appeal through `/appeal`. The system updates the submission status to `under_review`, records the creator's reasoning in the audit log, and returns a confirmation response.

---

# AI Tool Plan

## Milestone 3

Prompt AI to generate:

- Flask application skeleton
- POST /submit endpoint
- LLM detection function

Verification:

- Test endpoint using curl
- Verify JSON structure

---

## Milestone 4

Prompt AI to generate:

- Stylometric detection function
- Confidence scoring logic

Verification:

- Compare AI-generated and human-written examples
- Ensure scores differ meaningfully

---

## Milestone 5

Prompt AI to generate:

- Transparency label logic
- Appeal endpoint
- Audit log integration

Verification:

- Test all three label variants
- Verify appeal updates status correctly
- Verify audit log records submissions and appeals