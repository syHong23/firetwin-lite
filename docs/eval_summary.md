# Evaluation summary

Model: llama3.1:8b, temperature 0, 30 questions.

| Condition | Valid (all) | Valid (answerable) | Valid (traps) | Invented IDs | Wrong IDs | Missing IDs | LLM errors | Mean time (s) |
|---|---|---|---|---|---|---|---|---|
| A. LLM only | 5/30 | 1/24 | 4/6 | 22 | 11 | 48 | 0 | 5.2 |
| B. Grounded | 23/30 | 17/24 | 6/6 | 0 | 7 | 2 | 0 | 3.0 |
| C. Grounded + validated | 27/30 | 21/24 | 6/6 | 0 | 3 | 0 | 0 | 3.7 |
