import numpy as np

from nirikshak.detectors import ConformalThreshold, QBERThreshold
from nirikshak.scorecard import scorecard


def test_conformal_false_alarm_rate_holds_on_exchangeable_data():
    rng = np.random.default_rng(0)
    alpha = 0.05
    det = ConformalThreshold(alpha).fit(rng.normal(0.03, 0.005, 2000))
    honest = rng.normal(0.03, 0.005, 20000)
    assert det.predict(honest).mean() <= alpha + 0.01


def test_scorecard_counts():
    alarms = np.array([True, False, True, False])
    is_attack = np.array([True, True, False, False])
    assert scorecard(alarms, is_attack) == {"false_alarm_rate": 0.5, "miss_rate": 0.5}


def test_threshold_baseline():
    assert QBERThreshold().predict([0.05, 0.2]).tolist() == [False, True]
