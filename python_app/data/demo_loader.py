from pathlib import Path
from typing import Any
import pandas as pd


def load_demo_data() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parents[1] / "data" / "sample_nse_candidates.csv"
    return pd.read_csv(path).to_dict(orient="records")
