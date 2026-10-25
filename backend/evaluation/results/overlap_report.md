# Overlap assessment

Cases evaluated: 10 of 10

| Level | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Combination (overlap yes/no) | 8 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| Ingredient (moiety shared) | 8 | 0 | 0 | 1.0 | 1.0 | 1.0 |

Result-status accuracy (overlap_found / no_overlap_found / incomplete_data): 1.0
Medicines returned in request order: 10 of 10 cases

| Category | Cases | Status correct |
|---|---|---|
| salt_or_format_variant | 4 | 4 |
| multi | 3 | 3 |
| unrelated | 1 | 1 |
| incomplete_data | 1 | 1 |
| plain_exact | 1 | 1 |

## Failures

None.

Label caveat: Reconstructed preliminary overlap regression evaluation using verified BDDrugBank source IDs and current database mappings. Expected labels are provisional and have not been independently verified by a pharmacist. This is a developer regression set, not representative clinical validation.
