from pathlib import Path

import pandas as pd


DATA_PATH = Path(
    "data/interim/nasa_power_tanzania_daily.csv"
)


def test_output_exists():
    assert DATA_PATH.exists()


def test_output_not_empty():
    df = pd.read_csv(DATA_PATH)

    assert len(df) > 0


def test_required_columns_exist():
    df = pd.read_csv(DATA_PATH)

    required_columns = {
        "date",
        "location",
        "latitude",
        "longitude",
        "T2M",
        "T2M_MIN",
        "T2M_MAX",
        "RH2M",
        "PRECTOTCORR",
        "WS2M",
        "ALLSKY_SFC_SW_DWN",
    }

    assert required_columns.issubset(df.columns)