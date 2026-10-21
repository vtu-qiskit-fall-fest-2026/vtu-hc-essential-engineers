# Nirikshak: Project Dossier

**Nirikshak** (Hindi/Sanskrit: "inspector"). Catching real eavesdroppers on real quantum hardware.

| | |
|---|---|
| Event | Qiskit Fall Fest 2026, VTU Belagavi |
| Track | 1. Quantum Cryptography & Security |
| Duration | 48 hours (start: 21 Oct 2026, 3:00 PM IST) |
| Stack | Qiskit, Qiskit Aer, Qiskit IBM Runtime, scikit-learn / XGBoost, Streamlit |
| Hardware | IBM Quantum Open Plan (Heron r2, `ibm_kingston`) |

---

## 1. Project Title

**Nirikshak: A Hardware-in-the-Loop Stress Test and Drift-Robust Eavesdropper Detector for BB84 Quantum Key Distribution**

## 2. Problem Statement (one line)

Eavesdropper detectors for QKD are trained and tested almost entirely in simulation. Because nobody has measured whether they can tell normal hardware drift from a real attack on real quantum hardware, deployed QKD links risk false alarms that discard valid keys, or eavesdroppers who go undetected.

## 3. Problem Description

Quantum Key Distribution (QKD) lets two parties share a secret key with security guaranteed by physics: any eavesdropper disturbs the quantum states and raises the error rate. That guarantee only holds in practice if the system can reliably detect the eavesdropper. Today detection relies on a fixed error-rate threshold (about 11% for BB84) or on newer machine-learning detectors, and almost all of them are built and tested only on simulated data.

Real QKD links are not as clean as simulations. Their noise drifts with temperature, component aging and recalibration. Recent studies show that detectors trained in simulation lose much of their accuracy when operating conditions shift even slightly, and that partial attacks can stay below the standard threshold. This leaves two failure modes. The detector either mistakes normal drift for an attack and throws away valid keys, effectively a denial of service, or mistakes a real attack for normal noise and leaks the key to the eavesdropper.

Recent research names testing on real hardware data as an open problem, and European cybersecurity agencies have said QKD is not yet mature from a security perspective. Meanwhile, deployment is accelerating: India's National Quantum Mission has announced a 1,000 km QKD network, and DRDO has completed field and live-network trials. To our knowledge, no open benchmark measures how eavesdropper detectors perform on real quantum hardware, and no detector has been shown to keep its false-alarm rate stable under device drift while still catching attacks.

## 4. Proposed Solution (brief description)

Nirikshak is an open benchmark that tests BB84 eavesdropper detectors on real quantum hardware, together with a detector designed to stay reliable under device drift. It is built with Qiskit and run on IBM Quantum hardware (Heron r2).

1. **Real attacks on real qubits.** We run honest BB84 sessions and qubit-level attacks (full and partial intercept-resend, and an entangling-probe attack) on IBM hardware, using mid-circuit measurement and dynamic circuits, repeated across different qubits and sessions to capture real noise and drift.
2. **Simulation-to-hardware stress test.** Widely used detectors (the QBER threshold, Random Forest and XGBoost on temporal features, and a small quantum classifier) are trained on simulator data and evaluated on hardware data. We report miss rates at a fixed false-alarm budget, plus normal and worst-case results.
3. **Drift-robust detector.** Honest reference rounds interleaved with the key rounds and the backend's calibration data let the detector separate normal device drift from eavesdropping. Thresholds are set with conformal calibration, which gives a false-alarm rate we can state in advance.
4. **Open dataset and dashboard.** We release, to our knowledge, the first public dataset of hardware-generated BB84 attack logs, a reusable scorecard, and a live dashboard comparing a simulation-trained detector with Nirikshak on real hardware data.

**Scope note:** IBM's superconducting qubits provide real quantum noise and drift, and attacks run as real qubit operations. Optical-only attacks such as photon-number splitting and detector blinding are simulated and clearly labelled.

**Impact:** Nirikshak addresses gaps named in recent research on testing QKD detectors on hardware-generated data. It supports validating the eavesdropping detection behind India's growing QKD infrastructure, including the 1,000 km National Quantum Mission network and DRDO's field trials.

---

## 5. Technical Design

### 5.1 Components

| # | Component | Description |
|---|---|---|
| 1 | Protocol engine | BB84 rounds as Qiskit circuits; many rounds run in parallel on separate qubits in each shot; parameterized circuits for basis and attack sweeps |
| 2 | Attack library | Full intercept-resend, partial intercept, entangling probe (weak coupling to an ancilla), adaptive variants using `if_test`; simulated optical attacks (PNS, blinding) labelled as such |
| 3 | Noise and drift models | Aer noise models from backend calibration data; benign drift scenarios |
| 4 | Hardware runner | Qiskit IBM Runtime Sampler in job or batch mode on `ibm_kingston`; honest reference rounds interleaved with the key rounds |
| 5 | Feature extraction | Per-block QBER per basis, temporal moments, basis asymmetry, reference-round deviation, calibration features |
| 6 | Baseline detectors | 11% threshold, Random Forest, XGBoost, small quantum classifier (qiskit-machine-learning, optional) |
| 7 | Nirikshak detector | Drift-aware features plus conformal-calibrated thresholds with a stated false-alarm rate |
| 8 | Scorecard | Miss rate at a fixed false-alarm budget; normal vs shifted; worst case; sim-trained vs hardware-tested |
| 9 | Dashboard | Streamlit: live QBER, alarms, side-by-side baseline vs Nirikshak, attack injection |
| 10 | Open release | Hardware-generated dataset + dataset card + code |

### 5.2 Note on intercept-resend on hardware

Eve measures in her chosen basis, then undoes the basis rotation, which re-sends the state she measured. This needs mid-circuit measurement but not feed-forward. Feed-forward (`if_test`) is used only for adaptive attack variants.

---

## 6. Feasibility

### 6.1 Local machine (checked 21 Oct 2026)

| | |
|---|---|
| CPU | Intel Xeon Silver 4314, 8 cores |
| RAM | 78 GiB total (~52 GiB free at check time; other workloads using ~26 GiB) |
| GPU | NVIDIA RTX 6000 Ada, 48 GB, driver 570 (CUDA 12) |
| Disk | 178 GB free |
| OS / Python | Ubuntu 24.04, Python 3.12.3, uv available; Qiskit not yet installed |

All simulation, dataset generation, training, calibration and the dashboard fit comfortably. BB84 rounds use 1 to 2 qubits each. Use the stabilizer method for Clifford rounds; simulate entangling-probe rounds (non-Clifford) individually. Keep the quantum classifier small (4 to 8 qubits, sampled data).

### 6.2 IBM Quantum Open Plan (checked against IBM docs)

| Requirement | Status |
|---|---|
| Real hardware | 10 minutes (600 s) of quantum time free per rolling 28-day window (confirmed via `service.usage()`, 21 Oct 2026) |
| `ibm_kingston` (Heron r2) | Available to Open Plan users since March 2026 |
| Dynamic circuits (`if_test`) | "Available to all users on all backends" |
| Mid-circuit measurement (`MidCircuitMeasure` / `measure_2`) | Not on all backends; verify per account |
| Job and batch mode | Allowed |
| Session mode | **Not allowed** on Open Plan |
| Concurrent jobs | Max 3 running or queued per user |
| Feed-forward limits | ~2,400 one-bit broadcasts per job; operand of 32 bits or fewer; no nested `if`; no reset or measurement inside `if` |
| Usage counted | Quantum time only (not queue time); user-error failures still count |

Hour-0 check (after saving your own API key locally with `QiskitRuntimeService.save_account`):

```python
from qiskit_ibm_runtime import QiskitRuntimeService
service = QiskitRuntimeService()
print([b.name for b in service.backends(dynamic_circuits=True)])
print([b.name for b in service.backends(filters=lambda b: "measure_2" in b.supported_instructions)])
```

### 6.3 Installed and pinned (21 Oct 2026, see `requirements.lock`)

| Package | Version | Note |
|---|---|---|
| qiskit | 2.6.0 | IBM dynamic-circuit guide recommends `qiskit[all]~=2.5.2` or newer |
| qiskit-ibm-runtime | 0.50.0 | Guide recommends `~=0.49.0` or newer; includes `FakeKingston` for offline noise |
| qiskit-aer | 0.18.0 | Released 20 Oct 2026; all tests pass with it |
| scikit-learn / xgboost / streamlit | 1.9.1 / 3.4.1 / 1.66.0 | |
| qiskit-machine-learning | not installed | Optional extra `.[qml]`; Qiskit compatibility not yet checked |

Verified on this machine: 8/8 tests pass (noiseless QBER 0, full intercept-resend about 25%, partial intercept below 11%); the template transpiles to `FakeKingston` (rz/sx/measure) and simulates with Kingston noise; the dashboard runs without errors.

Known issue: qiskit-aer and scikit-learn each bundle `libgomp`; importing both raises "cannot allocate memory in static TLS block". Fix: `export GLIBC_TUNABLES=glibc.rtld.optional_static_tls=4096` (added to `.venv/bin/activate`).

---|---|---|
| qiskit | 2.6.0 | IBM dynamic-circuit guide recommends `qiskit[all]~=2.5.2` or newer |
| qiskit-ibm-runtime | guide recommends `~=0.49.0` or newer | Verify at install |
| qiskit-aer | 0.18.0 (released 20 Oct 2026) | Very new; fall back to the previous release if issues appear |
| qiskit-machine-learning | 0.9.1 (19 Aug 2026) | Qiskit compatibility not confirmed; keep optional |

---

## 7. 48-Hour Plan (team of 3)

| Hours | A: Quantum circuits and attacks | B: Data, ML and calibration | C: Frontend, docs and pitch |
|---|---|---|---|
| 0-3 | Environment, pinned versions, hour-0 IBM check | Feature spec, baseline skeleton | Dashboard skeleton |
| 3-10 | BB84 circuits, parallel-round layout, attack library (simulator) | Threshold baseline, simulated dataset generation | Live charts |
| 10-16 | **Submit hardware jobs early** (honest + attacks, interleaved reference rounds) | RF / XGBoost on simulated data | Attack-injection controls |
| 16-28 | Collect hardware runs across qubits/sessions | Hardware dataset assembly, sim-to-real stress test | Wire models to UI |
| 28-38 | Second hardware batch if budget allows | Nirikshak drift-aware detector + conformal calibration | Scorecard view, dataset card |
| 38-44 | Code freeze, reproducibility check | Results figures | README, slides |
| 44-48 | Demo rehearsal (3+ runs) | Demo rehearsal | Demo rehearsal |

### Hardware budget rules

- Test every circuit on the simulator before submitting.
- Run one small job first, read its actual usage, then scale.
- Combine circuits into few large jobs (3-job concurrency limit).
- Each team member uses their own free account.

---

## 8. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| IBM queue delays | Submit on day 1; small first job; simulator fallback with recorded hardware noise |
| Hardware minutes run out | Multiple accounts; parallel rounds per shot; parameterized circuits |
| `measure_2` unsupported | Use standard `measure` mid-circuit; verify in hour 0 |
| New package versions break | Pin versions in hour 0; fall back one release |
| QML classifier too slow | Keep it optional and small |
| Overclaiming | Label simulated optical attacks; use "to our knowledge"; report honest results even if classical wins |
| Judging rubric unknown | Get rules at kickoff; no official Fall Fest rubric was found |

---

## 9. References

### Prior work and gap
- EveSense, Qiskit Fall Fest 2026 @ MPSTME: https://github.com/ChiaraDeVenuto/evesense-qkd
- kameswarasai/qkd-anomaly-detection: https://github.com/kameswarasai/qkd-anomaly-detection
- Adaptive_QKD: https://github.com/sakshamg251206/Adaptive_QKD
- hybrid_qkd_pqc: https://github.com/bhuvand11/hybrid_qkd_pqc
- Q-Shield: https://github.com/thanmayee-7/Q-Shield
- qkd-krylov-detector: https://github.com/quantumspiritresearch-crypto/qkd-krylov-detector
- quantumshield-bb84: https://github.com/ezekieltony/quantumshield-bb84
- Beyond the QBER Threshold, arXiv 2608.04047: https://arxiv.org/abs/2608.04047
- Adversarial RL eavesdropping in BB84, arXiv 2606.22962: https://arxiv.org/pdf/2606.22962
- Resisting QKD attacks using QML, arXiv 2509.14282: https://arxiv.org/abs/2509.14282
- Adversarial learning game for QKD IDS, arXiv 2603.03502: https://arxiv.org/abs/2603.03502
- Deep anomaly detection for receiver attacks, arXiv 2508.12749: https://arxiv.org/abs/2508.12749
- QF-LOG simulation-based quantum forensics, arXiv 2610.25203: https://arxiv.org/abs/2610.25203
- QKD-Forensic-Dataset: https://github.com/MadhabCD/QKD-Forensic-Dataset
- Survey of DV/CV QKD defenses, arXiv 2605.27497: https://arxiv.org/html/2605.27497v1
- ML techniques for QKD review, arXiv 2603.07384: https://arxiv.org/pdf/2603.07384
- TARA conformal certification, arXiv 2512.04016: https://arxiv.org/pdf/2512.04016v1
- ML detection for CV-QKD hacking, Phys. Rev. A 107, 062422: https://link.aps.org/doi/10.1103/PhysRevA.107.062422
- GNN attack detection for CV-QKD, JOSA B: https://opg.optica.org/josab/abstract.cfm?uri=josab-41-6-1355
- Channel tampering in CV-QKD, Phys. Rev. Research 6, 023301: https://journals.aps.org/prresearch/abstract/10.1103/PhysRevResearch.6.023301
- Quantum k-NN for CV-QKD, Information 17, 763: https://doi.org/10.3390/info17080763
- Noise-resistant QML attack detection, arXiv 2601.06762: https://arxiv.org/abs/2601.06762
- BB84-like primitives on NISQ hardware, MDPI Electronics: https://www.mdpi.com/2079-9292/15/12/2534
- BB84 on PKTron and IBM hardware, Research Square: https://www.researchsquare.com/article/rs-10838323/v1
- QuDef SQOUT: https://quantumcomputingreport.com/qudef-launches-sqout-threat-intelligence-platform-for-quantum-communication-networks/

### QKD physics
- Quantum Cryptography: from Theory to Practice: https://arxiv.org/pdf/quant-ph/0702202
- Advances in Quantum Cryptography: https://arxiv.org/pdf/1906.01645
- Practical QKD state of the art: https://arxiv.org/pdf/1504.05471
- Finite-size decoy-state security proof (Quantum, 2026): https://quantum-journal.org/papers/q-2026-03-23-2037/

### Impact and policy
- ANSSI/BSI/NLNCSA/Swedish NCSA QKD position paper: https://cyber.gouv.fr/en/publications/jointly-led-international-publications/position-paper-on-quantum-key-distribution/
- NCSC 2018 QKD whitepaper (repost): https://danq.me/2018/08/03/qkd/
- ETSI QKD Protection Profile: https://www.telecomtv.com/content/security/etsi-releases-world-first-protection-profile-for-quantum-key-distribution-47346/
- QNu Labs 1,000 km milestone: https://www.qnulabs.com/news/indias-national-quantum-mission-crosses-1-000-km-quantum-communication-milestone-ahead-of-schedule
- C-DOT 14 quantum products: https://quantumcomputingreport.com/indias-c-dot-unveils-14-indigenous-quantum-products-during-43rd-foundation-day/
- DRDO QKD live-network test (ANI): https://aninews.in/news/national/general-news/drdo-successfully-tests-quantum-key-distributionqkd-platform-in-live-network20261014110557/
- DRDO QKD field trials (The Week): https://www.theweek.in/news/defence/2026/07/15/drdo-completes-military-field-trials-of-quantum-key-distribution-system-why-is-this-important.html
- Gidney RSA-2048 analysis: https://postquantum.com/quantum-research/quantum-breakthrough-rsa-2048/
- Q-Day Just Got Closer: https://thequantuminsider.com/2026/03/31/q-day-just-got-closer-three-papers-in-three-months-are-rewriting-the-quantum-threat-timeline/
- NIST IR 8547 (ABI Research): https://www.abiresearch.com/market-research/insight/7785443-nists-intention-to-deprecate-rsa-and-ecc-w
- NIST selects HQC: https://www.nist.gov/news-events/news/2025/03/nist-selects-hqc-fifth-algorithm-post-quantum-encryption
- India quantum-safe roadmap: https://postquantum.com/security-pqc/indias-quantum-safe-roadmap/

### IBM Quantum platform
- Plans overview: https://quantum.cloud.ibm.com/docs/guides/plans-overview
- Execution modes: https://quantum.cloud.ibm.com/docs/guides/execution-modes
- Execute dynamic circuits: https://quantum.cloud.ibm.com/docs/guides/execute-dynamic-circuits
- Classical feedforward and control flow: https://quantum.cloud.ibm.com/docs/guides/classical-feedforward-and-control-flow
- Workload usage: https://quantum.cloud.ibm.com/docs/en/administration/workloads
- Estimate job run time: https://quantum.cloud.ibm.com/docs/en/guides/estimate-job-run-time
- IBM Quantum pricing: https://www.ibm.com/quantum/pricing
- Open Plan promotion: https://quantumcomputingreport.com/ibm-offers-special-promotion-to-open-plan-users/

### Hackathon context
- UW-Madison Qiskit Fall Fest 2023 rules (similarity disqualification): https://wqi.wisc.edu/wqcc/qiskit-fall-fest-2023/quantum-hackathon
