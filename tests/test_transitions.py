import pandas as pd

from common.transitions import add_transition_events


def test_transition_events_only_fire_on_candidate_rising_edge():
    df = pd.DataFrame(
        {
            "Stage2A": [False, True, True, False, True],
            "Stage4A": [False, False, True, True, False],
        }
    )

    out = add_transition_events(df)

    assert list(out["Stage2A_Event"]) == [False, True, False, False, True]
    assert list(out["Stage4A_Event"]) == [False, False, True, False, False]
