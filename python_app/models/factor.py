from dataclasses import dataclass


@dataclass(frozen=True)
class Factor:
    name: str
    key: str
    weight: float
    low: float
    high: float
