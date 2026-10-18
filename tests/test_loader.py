import pytest
from pydantic import ValidationError

from app.data.loader import get_portfolio
from app.data.models import PortfolioData


def test_portfolio_json_loads():
    get_portfolio.cache_clear()
    portfolio = get_portfolio()
    assert portfolio.profile.name == "Sheikh Haseeb"
    assert len(portfolio.projects) == 4
    assert any(p.id == "consultancy-ai" for p in portfolio.projects)
    assert portfolio.experience[0].title == "AI/ML Engineer"
    assert portfolio.profile.current_status
    assert portfolio.profile.availability
    assert portfolio.profile.last_updated
    assert portfolio.experience[0].current is True
    assert portfolio.chat.suggestion_chips


def test_loader_validation_error_on_missing_fields():
    with pytest.raises(ValidationError):
        PortfolioData.model_validate({"profile": {}})

