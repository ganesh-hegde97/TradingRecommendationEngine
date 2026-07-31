from python_app.models import Stock
from python_app.services.recommendation_service import RecommendationService


def test_demo_workflow_returns_recommendations() -> None:
    recommendations = RecommendationService().screen_demo()
    assert recommendations
    assert all(isinstance(item.stock, Stock) for item in recommendations)
    assert recommendations == sorted(
        recommendations, key=lambda item: item.score, reverse=True
    )
