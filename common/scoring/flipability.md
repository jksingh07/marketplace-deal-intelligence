# Flipability Score Formula

**Version:** 1.0
**Status:** Active

The Flipability Score (0–100) estimates how easy it is to buy and resell a vehicle for profit with low risk. It is deterministic, stable, and explainable.

---

## 1. Core Formula

$$
\text{Base Score} = (0.55 \times \text{Value Score}) + (0.45 \times \text{Liquidity Score})
$$

$$
\text{Final Score} = \text{Round}(\text{Base Score} \times \text{Risk Multiplier})
$$

**Range:** 0 to 100.

---

## 2. Components

### A. Value Advantage Score (0–100)
Based on the discount relative to the estimated market price (P50).

| Deal Delta % | Score |
| :--- | :--- |
| $\le -5\%$ (Overpriced) | 10 |
| $-5\%$ to $0\%$ | 20 |
| $0\%$ to $5\%$ | 40 |
| $5\%$ to $10\%$ | 60 |
| $10\%$ to $20\%$ | 80 |
| $\ge 20\%$ (Bargain) | 95 |

$$
\text{Deal Delta \%} = \frac{\text{Market P50} - \text{Asking Price}}{\text{Market P50}}
$$

### B. Liquidity Proxy Score (0–100)
Based on the number of comparable listings found (market depth).

| Comps Count | Score |
| :--- | :--- |
| $\ge 50$ | 100 |
| $20 - 49$ | 80 |
| $10 - 19$ | 60 |
| $5 - 9$ | 45 |
| $< 5$ | 30 |

### C. Risk Multiplier (0.10–1.00)
A discount factor applied to the base score based on detected risks.
We take the **minimum** (most severe) multiplier from all detected signals.

**Verified Penalties:**

| Risk Type | Multiplier |
| :--- | :--- |
| **Accident / Title** | |
| Write-off, Salvage, WOVR | 0.25 |
| Structural/Flood/Airbag | 0.30 |
| Accident Damage | 0.60 |
| Hail Damage | 0.75 |
| **Legality** | |
| Defected, Unregistered | 0.35 |
| No RWC | 0.60 |
| Rego Expired | 0.70 |
| **Mechanical** | |
| Not Running, Knock, Gearbox | 0.45 |
| Leaks, Check Engine | 0.70 |
| **Mods** | |
| Stage 2+, E85, Swaps | 0.60 |
| Tuned, Bolt-ons | 0.75 |
| **Service History** | |
| None | 0.70 |
| Partial | 0.85 |

**Inferred Penalties:**
If a risk is *inferred* (not explicitly stated but implied), the penalty is softened:

$$
\text{Inferred Multiplier} = \frac{1.0 + \text{Verified Multiplier}}{2}
$$

*Example:* Verified Defect (0.35) → Inferred Defect (0.675).

---

## 3. Confidence Score (0–1)

Reflects how trustworthy the Flipability Score is.

**Base Confidence:**
| Comps | Confidence |
| :--- | :--- |
| $\ge 50$ | 0.9 |
| $20-49$ | 0.8 |
| $10-19$ | 0.7 |
| $5-9$ | 0.6 |
| $< 5$ | 0.5 |

**Penalties:**
- **-0.1** if `risk_level_overall` is unknown.
- **-0.1** if description is too short.

**Range:** Clamped between 0.3 and 0.95.
