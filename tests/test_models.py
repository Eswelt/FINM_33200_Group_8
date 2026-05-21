import numpy as np
import pandas as pd

from corn_forecast.models import _walk_forward_splits


def test_walk_forward_splits_expand_training_window():
    panel = pd.DataFrame(
        {
            "week": pd.date_range("2020-01-03", periods=30, freq="W-FRI"),
            "target_up_next": np.tile([0, 1], 15),
        }
    )

    folds = list(_walk_forward_splits(panel, "2020-03-27", test_window_weeks=4, retrain_step_weeks=4))

    assert len(folds) > 1
    assert folds[0][1]["week"].max() < folds[0][2]["week"].min()
    assert len(folds[1][1]) > len(folds[0][1])
