from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    REQUEST_TIMEOUT = 20
    CACHE_TTL = 900
    MAX_THREADS = 5
    DEFAULT_OUTPUT_DIR = "outputs"
    LOG_LEVEL = "INFO"


settings = Settings()
