## Provide Transparency

Label contributions containing AI-generated or AI-modified code with this
note above the generated code snipped and commit messages:

`Assisted-by: <tool>:<model>`

For example: `Assisted-by: Claude Code:claude-sonnet-4-6`

Use `unknown` if the exact tool or model identifier is unavailable. Never
guess.

## Methodological Correctness

Applies when you create or modify domain logic, algorithms, mathematics, statistics, scientific calculations, evaluation metrics, or research methodology:

* Explain the reasoning behind the approach.
* Explain why the apporach was chosen.
* State assumptions and limitations.
* State confidence level: High / Medium / Low.
* Never invent formulas, thresholds, metrics, or methodology without saying so.
* Never present uncertain methodological claims as facts.

Add this comment above methodological logic you create or modify:

```
""" 
Caution: Generated methodological logic; verification needed. 

Method summary: 
- [Briefly describe what this logic does] 

Reasoning:
- [Explain the reasoning why the approach was chosen]

Assumptions and Limitations: 
- [List assumptions and limitations here] 

Confidence Level: [High / Medium / Low] 
"""
```
