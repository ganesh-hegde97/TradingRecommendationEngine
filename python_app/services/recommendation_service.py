from python_app.config.logging_config import logger
from python_app.services.market_data_service import MarketDataService
from python_app.services.scoring_service import ScoringService
from python_app.models import Recommendation


class RecommendationService:
    def __init__(self):
        self.market_data_service = MarketDataService()
        self.scoring_service = ScoringService()

    def screen_demo(self) -> list[Recommendation]:
        logger.info("Running demo recommendation workflow")
        rows = self.market_data_service.load_demo()
        return self.scoring_service.score_candidates(rows)

    def screen_custom(self, symbols: list[str]) -> list[Recommendation]:
        logger.info("Running custom recommendation workflow")
        rows = self.market_data_service.download_custom(symbols)
        return self.scoring_service.score_candidates(rows)

    def screen_nifty50(self):
        logger.info("Running Nifty50 recommendation workflow")
        rows, source, failures = self.market_data_service.download_nifty50()
        recommendations = self.scoring_service.score_candidates(rows)
        return recommendations, source, failures
