import numpy as np
import pandas as pd
import pytest

from nirikshak.monitor import BlockRecord, LinkMonitor, NetworkMonitor, Verdict, from_session_table, read_jsonl, write_jsonl
from nirikshak.monitor.synthetic import LinkScenario, synthetic_stream


def test_record_validation_and_jsonl_roundtrip(tmp_path):
    with pytest.raises(ValueError):
        BlockRecord("L1", "2026-10-22T00:00:00", "other", 10, 1)
    with pytest.raises(ValueError):
        BlockRecord("L1", "2026-10-22T00:00:00", "key", 10, 11)
    recs = [BlockRecord("L1", "2026-10-22T00:00:00", "ref", 500, 9), BlockRecord("L1", "2026-10-22T00:01:00", "key", 480, 12)]
    path = tmp_path / "t.jsonl"
    assert write_jsonl(recs, path) == 2
    assert list(read_jsonl(path)) == recs
    assert recs[1].qber == 12 / 480


def test_window_closes_after_window_key_and_ref_blocks():
    mon = LinkMonitor("L1", window=20, n_perm=99)
    out = [mon.update(BlockRecord("L1", f"t{i}", "ref" if i % 2 == 0 else "key", 500, 8)) for i in range(40)]
    assert isinstance(out[-1], Verdict) and not any(isinstance(o, Verdict) for o in out[:-1])
    assert out[-1].key_blocks == out[-1].ref_blocks == 20
    assert mon.frozen_threshold is not None and mon.n_windows == 1


def test_honest_drift_keeps_budget_and_attack_is_caught():
    sc = [LinkScenario("drift", "drift", drift=lambda h: 0.03 * h / 24),
          LinkScenario("tap", "tap", attack_start_h=12, attack_fraction=1 / 16)]
    v = NetworkMonitor(n_perm=999).run(synthetic_stream(sc, hours=24, seed=1)).verdict_table()
    drift = v[v.link_id == "drift"]
    assert drift.alarm.mean() <= 0.2
    # a commissioning threshold frozen at the start floods with block alarms as the link drifts
    assert drift.blocks_flagged_frozen.sum() > 3 * drift.blocks_flagged.sum()
    tap = v[v.link_id == "tap"].reset_index(drop=True)
    assert tap.loc[13:, "alarm"].mean() >= 0.9
    assert v.blocks_flagged_11.sum() == 0


def test_from_session_table_interleaves_ref_and_key():
    rows = [{"session_id": s, "kind": k, "block": b, "qber": 0.02, "n_sifted": 500}
            for s in ("a", "b") for k in ("key", "ref") for b in range(3)]
    recs = from_session_table(pd.DataFrame(rows), "L5", "2026-10-22T00:00:00+05:30", pd.Timedelta(hours=1))
    assert [r.kind for r in recs[:4]] == ["ref", "key", "ref", "key"]
    assert len(recs) == 12 and all(r.errors == 10 for r in recs)
    assert pd.Timestamp(recs[6].t) > pd.Timestamp("2026-10-22T01:00:00+05:30")
    assert np.all(np.diff([pd.Timestamp(r.t).value for r in recs]) > 0)
