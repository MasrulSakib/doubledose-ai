# Overlap assessment

Cases evaluated: 36 of 36

| Level | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Combination (overlap yes/no) | 21 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| Ingredient (moiety shared) | 23 | 0 | 0 | 1.0 | 1.0 | 1.0 |

Result-status accuracy (overlap_found / no_overlap_found / incomplete_data): 1.0
Medicines returned in request order: 36 of 36 cases

| Category | Cases | Status correct |
|---|---|---|
| plain_exact | 6 | 6 |
| salt_or_format_variant | 10 | 10 |
| same_class_no_exact_overlap | 6 | 6 |
| unrelated | 2 | 2 |
| multi | 7 | 7 |
| incomplete_data | 5 | 5 |

## Failures

None.

Label caveat: Hand-labelled ingredient-overlap cases built from real records in data/medicine.csv. Labels were written by the developer's assistant from the generic-name column using standard pharmacology (same active moiety = overlap; same class but different moiety = no exact overlap). They have NOT been verified by a pharmacist.
