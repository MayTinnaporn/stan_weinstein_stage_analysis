import pandas as pd

from common.transitions import add_transition_events
from crypto.transitions import add_crypto_transition_semantics


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


def test_crypto_episode_events_and_confirmation_are_causal():
    df = pd.DataFrame(
        {
            "Close": [90, 110, 105, 115, 95, 110, 105, 45, 44],
            "Stage": [1, 2, 2, 2, 1, 3, 3, 4, 4],
            "Resistance_26w": [100] * 9,
            "Support_26w": [50] * 9,
            "Stage2A": [False, True, False, True, False, True, False, False, False],
            "Stage4A": [False, False, False, False, False, False, False, True, False],
        }
    )
    out = add_crypto_transition_semantics(add_transition_events(df))

    assert list(out["Stage2A_EpisodeStart_Event"]) == [
        False,
        True,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
    ]
    assert out.loc[3, "Stage2A_Continuation_Event"]
    assert out.loc[2, "Stage2A_Confirmed_Event"]
    assert not out.loc[1, "Stage2A_Confirmed_Event"]
    assert out.loc[6, "Stage2A_FailedConfirmation_Event"]
    assert out.loc[8, "Stage4A_Confirmed_Event"]
    assert out.loc[3, "Weeks_Since_Stage2A_Event"] == 2
    assert out.loc[3, "Weeks_In_Stage"] == 3


def test_confirmation_does_not_use_the_candidate_week_close():
    df = pd.DataFrame(
        {
            "Close": [90, 120],
            "Stage": [1, 2],
            "Resistance_26w": [100, 100],
            "Support_26w": [50, 50],
            "Stage2A": [False, True],
            "Stage4A": [False, False],
        }
    )
    out = add_crypto_transition_semantics(add_transition_events(df))

    assert out.loc[1, "Stage2A_EpisodeStart_Event"]
    assert not out["Stage2A_Confirmed_Event"].any()
    assert not out["Stage2A_FailedConfirmation_Event"].any()
