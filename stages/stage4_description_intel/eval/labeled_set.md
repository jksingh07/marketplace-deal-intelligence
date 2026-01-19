# Labeled Evaluation Set

This file contains labeled examples for evaluating Stage 4 performance.

## Labeling Criteria

Label the following for each listing:
1. **Write-off/Accident signals** (present/absent)
2. **Defect/Rego/RWC signals** (present/absent)
3. **High-risk mods** (present/absent, type)
4. **Major mechanical issues** (list)

## Evaluation Metrics

- Precision: % of flagged signals that are correct
- Recall: % of actual signals that were caught
- Hallucination rate: % of LLM-extracted issues not in text

## Target Performance

**High Priority (Must be reliable):**
- Write-off signals: Precision > 0.95, Recall > 0.90
- Defect/rego signals: Precision > 0.95, Recall > 0.90

**Medium Priority:**
- High-risk mods: Precision > 0.85, Recall > 0.80
- Major mechanical issues: Precision > 0.80, Recall > 0.75

## Labeled Examples

*[This file should contain actual labeled listing examples once evaluation begins]*

Format:
```markdown
## Listing ID: {id}
**Text:** {description excerpt}
**Labels:**
- Write-off: Yes/No
- Defect/Rego: Yes/No
- High-risk mods: [list]
- Major mechanical: [list]
```
