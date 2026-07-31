from python_app.data.demo_loader import load_demo_data
from python_app.models import Stock


def test_demo_loader_returns_stock_models() -> None:
    stocks = load_demo_data()
    assert len(stocks) == 10
    assert all(isinstance(stock, Stock) for stock in stocks)
    assert all(stock.symbol for stock in stocks)
