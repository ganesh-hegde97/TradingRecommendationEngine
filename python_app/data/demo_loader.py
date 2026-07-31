from pathlib import Path
import pandas as pd
from python_app.models import Stock


def load_demo_data() -> list[Stock]:
    path = Path(__file__).resolve().parents[2] / "data" / "sample_nse_candidates.csv"
    return [
        Stock.from_mapping(row) for row in pd.read_csv(path).to_dict(orient="records")
    ]
