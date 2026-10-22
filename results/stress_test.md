# Stress test: alarm rates per condition (alpha = 5%)

Honest rows are false-alarm rates (target <= 5%); other rows are detection rates.
All detectors except Nirikshak were trained or calibrated on `data/sim/train.parquet`.

## sim: training conditions

| Condition | 11% rule | sim-calibrated threshold | Random Forest (sim-trained) | XGBoost (sim-trained) | XGBoost + reference features | Nirikshak |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| honest (false alarms) | 0% | 6% | 5% | 6% | 7% | 7% |
| intercept 1/16 rounds | 0% | 60% | 53% | 60% | 58% | 51% |
| intercept 2/16 rounds | 0% | 92% | 92% | 92% | 92% | 90% |
| intercept 4/16 rounds | 4% | 99% | 100% | 100% | 100% | 100% |
| intercept 8/16 rounds | 84% | 100% | 100% | 100% | 100% | 100% |
| entangling probe (all) | 0% | 53% | 46% | 49% | 51% | 50% |

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

## hardware: ibm_kingston batch 2 (timing matched, plain idle)

| Condition | 11% rule | sim-calibrated threshold | Random Forest (sim-trained) | XGBoost (sim-trained) | XGBoost + reference features | Nirikshak |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| honest (false alarms) | 0% | 82% | 87% | 88% | 25% | 5% |
| intercept 1/16 rounds | 0% | 100% | 100% | 100% | 70% | 30% |
| intercept 2/16 rounds | 5% | 100% | 100% | 100% | 100% | 15% |
| intercept 4/16 rounds | 45% | 100% | 100% | 100% | 100% | 100% |
| intercept 8/16 rounds | 100% | 100% | 100% | 100% | 100% | 100% |
| entangling probe (all) | 0% | 95% | 92% | 92% | 62% | 30% |

## hardware: ibm_kingston batch 3 (timing matched, spin echo)

| Condition | 11% rule | sim-calibrated threshold | Random Forest (sim-trained) | XGBoost (sim-trained) | XGBoost + reference features | Nirikshak |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| honest (false alarms) | 0% | 2% | 2% | 3% | 5% | 0% |
| intercept 1/16 rounds | 0% | 55% | 50% | 60% | 75% | 60% |
| intercept 2/16 rounds | 0% | 95% | 95% | 100% | 100% | 95% |
| intercept 4/16 rounds | 5% | 100% | 100% | 100% | 100% | 100% |
| intercept 8/16 rounds | 95% | 100% | 100% | 100% | 100% | 100% |
| entangling probe (all) | 0% | 97% | 92% | 93% | 90% | 83% |

## hardware: ibm_kingston batch 4 (timing matched, spin echo)

| Condition | 11% rule | sim-calibrated threshold | Random Forest (sim-trained) | XGBoost (sim-trained) | XGBoost + reference features | Nirikshak |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| honest (false alarms) | 0% | 3% | 2% | 7% | 3% | 0% |
| intercept 1/16 rounds | 0% | 45% | 45% | 45% | 45% | 45% |
| intercept 2/16 rounds | 0% | 90% | 85% | 90% | 90% | 85% |
| intercept 4/16 rounds | 10% | 100% | 100% | 100% | 100% | 100% |
| intercept 8/16 rounds | 90% | 100% | 100% | 100% | 100% | 100% |
| entangling probe (all) | 0% | 87% | 90% | 93% | 83% | 83% |
