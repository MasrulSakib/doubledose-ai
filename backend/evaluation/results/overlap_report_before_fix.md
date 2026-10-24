# Overlap assessment

Cases evaluated: 36 of 36

| Level | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Combination (overlap yes/no) | 13 | 0 | 8 | 1.0 | 0.619 | 0.765 |
| Ingredient (moiety shared) | 14 | 0 | 9 | 1.0 | 0.609 | 0.757 |

Result-status accuracy (overlap_found / no_overlap_found / incomplete_data): 0.778
Medicines returned in request order: 19 of 36 cases

| Category | Cases | Status correct |
|---|---|---|
| plain_exact | 6 | 6 |
| salt_or_format_variant | 10 | 2 |
| same_class_no_exact_overlap | 6 | 6 |
| unrelated | 2 | 2 |
| multi | 7 | 7 |
| incomplete_data | 5 | 5 |

## Failures

- S01 (Amoxicillin Trihydrate vs Amoxicillin (co-amoxiclav)): expected ['amoxicillin'] / overlap_found, got none / no_overlap_found
- S02 (Atorvastatin Calcium vs Atorvastatin): expected ['atorvastatin'] / overlap_found, got none / no_overlap_found
- S03 (Amlodipine Besilate vs Amlodipine): expected ['amlodipine'] / overlap_found, got none / no_overlap_found
- S04 (Metformin Hydrochloride vs Metformin): expected ['metformin'] / overlap_found, got none / no_overlap_found
- S05 (Esomeprazole vs Esomeprazole Magnesium (with naproxen)): expected ['esomeprazole'] / overlap_found, got none / no_overlap_found
- S06 (Diclofenac Potassium vs Diclofenac Sodium): expected ['diclofenac'] / overlap_found, got none / no_overlap_found
- S07 (name stored with non-breaking spaces): expected ['tramadol'] / overlap_found, got none / no_overlap_found
- S08 (name stored with a double space): expected ['tamsulosin'] / overlap_found, got none / no_overlap_found
- M07 (two singles plus their combination): expected ['glimepiride', 'metformin'] / overlap_found, got ['glimepiride'] / overlap_found

Label caveat: Hand-labelled ingredient-overlap cases built from real records in data/medicine.csv. Labels were written by the developer's assistant from the generic-name column using standard pharmacology (same active moiety = overlap; same class but different moiety = no exact overlap). They have NOT been verified by a pharmacist.
