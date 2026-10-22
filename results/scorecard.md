# Nirikshak scorecard

False-alarm budget alpha = 5%. Rates show exact 95% intervals in brackets.
Key rate: asymptotic BB84, secret bits per sifted bit; 0 means the protocol would abort.

## Real hardware, per session

### `ibm_kingston` batch 1 (timing not matched, job `dbcdge9gv2cc73ea4ne0`)

Not used for claims: rounds Eve did not touch picked up extra noise.

| Session | Key QBER | Reference QBER | Key rate | Nirikshak blocks | 11% rule blocks | Session p-value | Session verdict |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| honest | 0.7% | 0.7% | 0.88 | 2/20 | 0/20 | 0.5981 | clean |
| honest | 0.8% | 0.7% | 0.87 | 0/20 | 0/20 | 0.3187 | clean |
| honest | 0.7% | 1.0% | 0.87 | 0/20 | 0/20 | 0.9622 | clean |
| intercept 1/16 | 5.7% | 0.9% | 0.37 | 20/20 | 0/20 | 0.0001 | **attack** |
| intercept 2/16 | 5.6% | 0.7% | 0.38 | 20/20 | 0/20 | 0.0001 | **attack** |
| intercept 4/16 | 10.8% | 0.8% | 0.01 | 20/20 | 9/20 | 0.0001 | **attack** |
| intercept 8/16 | 16.5% | 0.8% | 0.00 | 20/20 | 19/20 | 0.0001 | **attack** |
| probe pi/8, 16/16 | 4.3% | 1.0% | 0.49 | 20/20 | 0/20 | 0.0001 | **attack** |
| probe pi/4, 8/16 | 4.5% | 0.9% | 0.47 | 20/20 | 0/20 | 0.0001 | **attack** |
| probe pi/4, 16/16 | 5.1% | 0.8% | 0.42 | 20/20 | 0/20 | 0.0001 | **attack** |

### `ibm_kingston` batch 2 (timing matched, plain idle, job `dbcdpek24mrc73cjedeg`)

Not used for claims: plain idle raised the noise floor (superseded by spin echo).

| Session | Key QBER | Reference QBER | Key rate | Nirikshak blocks | 11% rule blocks | Session p-value | Session verdict |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| honest | 4.3% | 4.2% | 0.49 | 0/20 | 0/20 | 0.4022 | clean |
| honest | 3.9% | 4.7% | 0.53 | 0/20 | 0/20 | 0.9709 | clean |
| honest | 4.4% | 4.0% | 0.48 | 3/20 | 0/20 | 0.1602 | clean |
| intercept 1/16 | 6.0% | 4.2% | 0.35 | 6/20 | 0/20 | 0.0008 | **attack** |
| intercept 2/16 | 7.6% | 4.3% | 0.23 | 3/20 | 1/20 | 0.0001 | **attack** |
| intercept 4/16 | 10.8% | 4.2% | 0.01 | 20/20 | 9/20 | 0.0001 | **attack** |
| intercept 8/16 | 15.0% | 4.6% | 0.00 | 20/20 | 20/20 | 0.0001 | **attack** |
| probe pi/8, 16/16 | 4.1% | 3.2% | 0.51 | 1/20 | 0/20 | 0.0013 | **attack** |
| probe pi/4, 8/16 | 4.2% | 3.0% | 0.50 | 3/20 | 0/20 | 0.0005 | **attack** |
| probe pi/4, 16/16 | 5.5% | 3.0% | 0.39 | 14/20 | 0/20 | 0.0001 | **attack** |

### `ibm_kingston` batch 3 (timing matched, spin echo, job `dbcdsck24mrc73cjek9g`)

| Session | Key QBER | Reference QBER | Key rate | Nirikshak blocks | 11% rule blocks | Session p-value | Session verdict |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| honest | 1.7% | 1.5% | 0.76 | 0/20 | 0/20 | 0.2361 | clean |
| honest | 1.8% | 1.9% | 0.74 | 0/20 | 0/20 | 0.5776 | clean |
| honest | 1.8% | 2.0% | 0.75 | 0/20 | 0/20 | 0.8721 | clean |
| intercept 1/16 | 3.1% | 1.5% | 0.60 | 12/20 | 0/20 | 0.0001 | **attack** |
| intercept 2/16 | 4.9% | 1.5% | 0.43 | 19/20 | 0/20 | 0.0001 | **attack** |
| intercept 4/16 | 7.8% | 1.7% | 0.21 | 20/20 | 1/20 | 0.0001 | **attack** |
| intercept 8/16 | 15.1% | 1.7% | 0.00 | 20/20 | 19/20 | 0.0001 | **attack** |
| probe pi/8, 16/16 | 4.5% | 1.8% | 0.47 | 20/20 | 0/20 | 0.0001 | **attack** |
| probe pi/4, 8/16 | 3.8% | 1.9% | 0.53 | 10/20 | 0/20 | 0.0001 | **attack** |
| probe pi/4, 16/16 | 5.5% | 1.7% | 0.39 | 20/20 | 0/20 | 0.0001 | **attack** |

### `ibm_kingston` batch 4 (timing matched, spin echo, job `dbce8c0c77vs738641j0`)

| Session | Key QBER | Reference QBER | Key rate | Nirikshak blocks | 11% rule blocks | Session p-value | Session verdict |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| honest | 1.7% | 1.7% | 0.75 | 0/20 | 0/20 | 0.4993 | clean |
| honest | 1.7% | 1.8% | 0.75 | 0/20 | 0/20 | 0.7496 | clean |
| honest | 1.8% | 1.7% | 0.74 | 0/20 | 0/20 | 0.2976 | clean |
| intercept 1/16 | 3.0% | 1.7% | 0.61 | 9/20 | 0/20 | 0.0002 | **attack** |
| intercept 2/16 | 4.8% | 1.8% | 0.45 | 17/20 | 0/20 | 0.0001 | **attack** |
| intercept 4/16 | 7.8% | 1.9% | 0.21 | 20/20 | 2/20 | 0.0001 | **attack** |
| intercept 8/16 | 14.2% | 1.7% | 0.00 | 20/20 | 18/20 | 0.0001 | **attack** |
| probe pi/8, 16/16 | 4.1% | 2.0% | 0.51 | 15/20 | 0/20 | 0.0001 | **attack** |
| probe pi/4, 8/16 | 3.8% | 1.9% | 0.53 | 15/20 | 0/20 | 0.0001 | **attack** |
| probe pi/4, 16/16 | 5.2% | 1.8% | 0.41 | 20/20 | 0/20 | 0.0001 | **attack** |

### `ibm_kingston` batch 5 (timing matched, spin echo, job `dbd0vo424mrc73cki1l0`)

| Session | Key QBER | Reference QBER | Key rate | Nirikshak blocks | 11% rule blocks | Session p-value | Session verdict |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| honest | 1.7% | 1.7% | 0.75 | 3/20 | 0/20 | 0.5273 | clean |
| honest | 1.7% | 1.5% | 0.75 | 2/20 | 0/20 | 0.1687 | clean |
| honest | 1.9% | 1.8% | 0.73 | 3/20 | 0/20 | 0.3774 | clean |
| intercept 1/16 | 3.2% | 1.8% | 0.59 | 7/20 | 0/20 | 0.0001 | **attack** |
| intercept 2/16 | 5.1% | 1.8% | 0.42 | 18/20 | 0/20 | 0.0001 | **attack** |
| intercept 4/16 | 8.5% | 1.8% | 0.16 | 20/20 | 4/20 | 0.0001 | **attack** |
| intercept 8/16 | 15.4% | 1.9% | 0.00 | 20/20 | 20/20 | 0.0001 | **attack** |
| probe pi/8, 16/16 | 3.7% | 1.9% | 0.54 | 15/20 | 0/20 | 0.0001 | **attack** |
| probe pi/4, 8/16 | 3.7% | 2.0% | 0.55 | 12/20 | 0/20 | 0.0001 | **attack** |
| probe pi/4, 16/16 | 5.3% | 2.0% | 0.41 | 19/20 | 0/20 | 0.0001 | **attack** |

### `ibm_marrakesh` batch 7 (timing matched, spin echo, job `dbd3bts24mrc73cklb10`)

| Session | Key QBER | Reference QBER | Key rate | Nirikshak blocks | 11% rule blocks | Session p-value | Session verdict |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| honest | 3.5% | 3.4% | 0.56 | 0/20 | 0/20 | 0.3206 | clean |
| honest | 3.9% | 3.8% | 0.52 | 2/20 | 0/20 | 0.2837 | clean |
| honest | 3.5% | 3.8% | 0.56 | 0/20 | 0/20 | 0.8839 | clean |
| intercept 1/16 | 4.9% | 3.9% | 0.43 | 1/20 | 0/20 | 0.0035 | **attack** |
| intercept 2/16 | 7.0% | 3.2% | 0.27 | 17/20 | 0/20 | 0.0001 | **attack** |
| intercept 4/16 | 9.5% | 3.6% | 0.10 | 20/20 | 2/20 | 0.0001 | **attack** |
| intercept 8/16 | 15.0% | 3.1% | 0.00 | 20/20 | 19/20 | 0.0001 | **attack** |
| probe pi/8, 16/16 | 10.2% | 3.6% | 0.05 | 20/20 | 8/20 | 0.0001 | **attack** |
| probe pi/4, 8/16 | 7.6% | 3.6% | 0.22 | 19/20 | 2/20 | 0.0001 | **attack** |
| probe pi/4, 16/16 | 11.4% | 3.7% | 0.00 | 20/20 | 11/20 | 0.0001 | **attack** |

## Real hardware, `ibm_kingston`, pooled over 3 spin-echo batch(es)

Honest row: false alarms. Other rows: detection.

| Condition | Blocks | Nirikshak, per block | 11% rule, per block | Nirikshak, per session |
| :--- | :-: | :-: | :-: | :-: |
| honest | 180 | 4% (2%-9%) | 0% (0%-2%) | 0% (0%-34%) |
| intercept 1/16 | 60 | 47% (34%-60%) | 0% (0%-6%) | 100% (29%-100%) |
| intercept 2/16 | 60 | 90% (79%-96%) | 0% (0%-6%) | 100% (29%-100%) |
| intercept 4/16 | 60 | 100% (94%-100%) | 12% (5%-23%) | 100% (29%-100%) |
| intercept 8/16 | 60 | 100% (94%-100%) | 95% (86%-99%) | 100% (29%-100%) |
| probe pi/8, 16/16 | 60 | 83% (71%-92%) | 0% (0%-6%) | 100% (29%-100%) |
| probe pi/4, 8/16 | 60 | 62% (48%-74%) | 0% (0%-6%) | 100% (29%-100%) |
| probe pi/4, 16/16 | 60 | 98% (91%-100%) | 0% (0%-6%) | 100% (29%-100%) |

## Real hardware, `ibm_marrakesh`, pooled over 1 spin-echo batch(es)

Honest row: false alarms. Other rows: detection.

| Condition | Blocks | Nirikshak, per block | 11% rule, per block | Nirikshak, per session |
| :--- | :-: | :-: | :-: | :-: |
| honest | 60 | 3% (0%-12%) | 0% (0%-6%) | 0% (0%-71%) |
| intercept 1/16 | 20 | 5% (0%-25%) | 0% (0%-17%) | 100% (3%-100%) |
| intercept 2/16 | 20 | 85% (62%-97%) | 0% (0%-17%) | 100% (3%-100%) |
| intercept 4/16 | 20 | 100% (83%-100%) | 10% (1%-32%) | 100% (3%-100%) |
| intercept 8/16 | 20 | 100% (83%-100%) | 95% (75%-100%) | 100% (3%-100%) |
| probe pi/8, 16/16 | 20 | 100% (83%-100%) | 40% (19%-64%) | 100% (3%-100%) |
| probe pi/4, 8/16 | 20 | 95% (75%-100%) | 10% (1%-32%) | 100% (3%-100%) |
| probe pi/4, 16/16 | 20 | 100% (83%-100%) | 55% (32%-77%) | 100% (3%-100%) |

## Simulation, session verdict

Honest rows: share of honest sessions wrongly flagged (target 5% or less).

### training conditions

| Condition | Sessions | Session verdict | Per block (Nirikshak) |
| :--- | :-: | :-: | :-: |
| honest | 30 | 13% (4%-31%) | 7% (5%-9%) |
| intercept 1/16 | 10 | 100% (69%-100%) | 51% (44%-58%) |
| intercept 2/16 | 10 | 100% (69%-100%) | 90% (84%-93%) |
| intercept 4/16 | 10 | 100% (69%-100%) | 100% (98%-100%) |
| intercept 8/16 | 10 | 100% (69%-100%) | 100% (98%-100%) |
| probe pi/8, 16/16 | 10 | 100% (69%-100%) | 21% (16%-27%) |
| probe pi/4, 8/16 | 10 | 100% (69%-100%) | 48% (41%-55%) |
| probe pi/4, 16/16 | 10 | 100% (69%-100%) | 80% (73%-85%) |

### drifted noise

| Condition | Sessions | Session verdict | Per block (Nirikshak) |
| :--- | :-: | :-: | :-: |
| honest | 15 | 0% (0%-22%) | 2% (1%-5%) |
| intercept 1/16 | 5 | 80% (28%-99%) | 31% (22%-41%) |
| intercept 2/16 | 5 | 100% (48%-100%) | 60% (50%-70%) |
| intercept 4/16 | 5 | 100% (48%-100%) | 92% (85%-96%) |
| intercept 8/16 | 5 | 100% (48%-100%) | 100% (96%-100%) |
| probe pi/8, 16/16 | 5 | 80% (28%-99%) | 30% (21%-40%) |
| probe pi/4, 8/16 | 5 | 60% (15%-95%) | 18% (11%-27%) |
| probe pi/4, 16/16 | 5 | 100% (48%-100%) | 47% (37%-57%) |

### Kingston noise snapshot

| Condition | Sessions | Session verdict | Per block (Nirikshak) |
| :--- | :-: | :-: | :-: |
| honest | 6 | 0% (0%-46%) | 8% (3%-14%) |
| intercept 1/16 | 2 | 100% (16%-100%) | 78% (62%-89%) |
| intercept 2/16 | 2 | 100% (16%-100%) | 100% (91%-100%) |
| intercept 4/16 | 2 | 100% (16%-100%) | 100% (91%-100%) |
| intercept 8/16 | 2 | 100% (16%-100%) | 100% (91%-100%) |
| probe pi/8, 16/16 | 2 | 100% (16%-100%) | 100% (91%-100%) |
| probe pi/4, 8/16 | 2 | 100% (16%-100%) | 98% (87%-100%) |
| probe pi/4, 16/16 | 2 | 100% (16%-100%) | 100% (91%-100%) |

### drifted noise, honest sessions only

| Condition | Sessions | Session verdict | Per block (Nirikshak) |
| :--- | :-: | :-: | :-: |
| honest | 200 | 6% (4%-11%) | 4% (4%-5%) |

### training conditions, honest sessions only

| Condition | Sessions | Session verdict | Per block (Nirikshak) |
| :--- | :-: | :-: | :-: |
| honest | 400 | 5% (3%-8%) | 5% (4%-5%) |
