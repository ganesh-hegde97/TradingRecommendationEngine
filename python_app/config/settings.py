from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Global application configuration."""

    APP_NAME: str = "Trading Recommendation Engine"
    APP_VERSION: str = "2.0"
    OUTPUT_DIRECTORY: str = "outputs"
    LOG_DIRECTORY: str = "logs"
    CACHE_DIRECTORY: str = ".cache"
    REQUEST_TIMEOUT: int = 20
    CACHE_TTL_SECONDS: int = 900
    MAX_DOWNLOAD_THREADS: int = 5
    DEFAULT_SCORE_THRESHOLD: int = 70
    DEFAULT_EXCEL_FILE: str = "recommendations.xlsx"
    LOG_LEVEL: str = "INFO"
    DATA_HISTORY_PERIOD: str = "6mo"
    DATA_INTERVAL: str = "1d"
    BASE_PATH: Path = Path(__file__).resolve().parent.parent
    NIFTY50_CONSTITUENT_URL = (
        "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
    )
    NIFTY50_OFFICIAL_PAGE = (
        "https://www.niftyindices.com/indices/equity/broad-based-indices/nifty--50"
    )


settings = Settings()
