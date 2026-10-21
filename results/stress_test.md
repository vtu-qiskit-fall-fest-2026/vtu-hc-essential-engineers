# Stress test: alarm rates per condition (alpha = 5%)

Honest rows are false-alarm rates (target <= 5%); other rows are detection rates.
All detectors except Nirikshak were trained or calibrated on `data/sim/train.parquet`.

## sim: drifted noise

| Condition | 11% rule | sim-calibrated threshold | Random Forest (sim-trained) | XGBoost (sim-trained) | XGBoost + reference features | Nirikshak |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| honest (false alarms) | 1% | 88% | 84% | 84% | 20% | 2% |
| intercept 1/16 rounds | 6% | 96% | 94% | 96% | 58% | 31% |
| intercept 2/16 rounds | 13% | 100% | 100% | 100% | 89% | 60% |
| intercept 4/16 rounds | 68% | 100% | 100% | 100% | 99% | 92% |
| intercept 8/16 rounds | 95% | 100% | 100% | 100% | 100% | 100% |
| entangling probe (all) | 2% | 93% | 91% | 92% | 55% | 32% |

## sim: Kingston noise snapshot

| Condition | 11% rule | sim-calibrated threshold | Random Forest (sim-trained) | XGBoost (sim-trained) | XGBoost + reference features | Nirikshak |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| honest (false alarms) | 0% | 0% | 0% | 0% | 2% | 8% |
| intercept 1/16 rounds | 0% | 22% | 25% | 28% | 65% | 78% |
| intercept 2/16 rounds | 0% | 75% | 70% | 75% | 100% | 100% |
| intercept 4/16 rounds | 2% | 100% | 100% | 100% | 100% | 100% |
| intercept 8/16 rounds | 85% | 100% | 100% | 100% | 100% | 100% |
| entangling probe (all) | 0% | 73% | 74% | 75% | 92% | 99% |

## hardware: ibm_kingston batch 1 (timing NOT matched)

| Condition | 11% rule | sim-calibrated threshold | Random Forest (sim-trained) | XGBoost (sim-trained) | XGBoost + reference features | Nirikshak |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| honest (false alarms) | 0% | 0% | 0% | 0% | 0% | 3% |
| intercept 1/16 rounds | 0% | 100% | 100% | 100% | 100% | 100% |
| intercept 2/16 rounds | 0% | 95% | 90% | 90% | 100% | 100% |
| intercept 4/16 rounds | 45% | 100% | 100% | 100% | 100% | 100% |
| intercept 8/16 rounds | 95% | 100% | 100% | 100% | 100% | 100% |
| entangling probe (all) | 0% | 98% | 95% | 95% | 100% | 100% |
