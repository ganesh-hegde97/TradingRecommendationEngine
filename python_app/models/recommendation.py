from dataclasses import dataclass
from python_app.models import Stock


@dataclass
class Recommendation:
    stock: Stock
    score: float
    decision: str
    confidence: float
    reasons: list[str]
