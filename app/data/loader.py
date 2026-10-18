import json
import logging
from functools import lru_cache
from pathlib import Path

from app.data.models import PortfolioData

logger = logging.getLogger(__name__)
PORTFOLIO_JSON = Path(__file__).parent / "portfolio.json"


@lru_cache
def get_portfolio() -> PortfolioData:
    logger.debug("Loading portfolio data from %s", PORTFOLIO_JSON)
    raw = json.loads(PORTFOLIO_JSON.read_text(encoding="utf-8"))
    portfolio = PortfolioData.model_validate(raw)
    logger.info(
        "Portfolio loaded | name=%s | projects=%d | assistant=%s",
        portfolio.profile.name,
        len(portfolio.projects),
        portfolio.assistant.name,
    )
    return portfolio
