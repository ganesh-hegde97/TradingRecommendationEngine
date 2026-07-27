import logging
from pathlib import Path

from python_app.config.settings import settings

LOG_FOLDER = settings.BASE_PATH / settings.LOG_DIRECTORY
LOG_FOLDER.mkdir(exist_ok=True)
LOG_FILE = LOG_FOLDER / "application.log"
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(settings.APP_NAME)
