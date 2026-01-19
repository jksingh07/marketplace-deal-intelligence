# Question Generator Prompt

Generate actionable follow-up questions based on listing content and gaps.

## Purpose

Generate questions that help buyers:
1. Fill information gaps
2. Verify claims
3. Assess risk
4. Negotiate effectively

## Input

Listing details:
- Title: {title}
- Description: {description}
- Extracted signals: {extracted_signals}

## Instructions

Generate concrete, actionable questions the buyer should ask the seller.

**Question Types:**

1. **Missing Critical Information**
   - Service history gaps
   - Ownership history
   - Usage patterns

2. **Verification Questions**
   - Claims about condition
   - Maintenance evidence
   - Modifications details

3. **Risk Assessment**
   - Mechanical issues details
   - Accident/write-off specifics
   - Legality confirmations

4. **Negotiation Questions**
   - Reason for selling
   - Price flexibility
   - Urgency level

## Output Format

Array of strings, each a complete question:
- Be specific and actionable
- Avoid yes/no questions when possible
- Focus on high-value information

Example:
```json
{
  "missing_info_questions": [
    "What is the service history since [year]?",
    "Has the vehicle been in any accidents?"
  ],
  "recommended_questions_to_ask": [
    "Can you provide service receipts from the last 3 years?",
    "Why are you selling the vehicle?",
    "What modifications have been made and by whom?",
    "Is there a current RWC, and when does rego expire?"
  ]
}
```
