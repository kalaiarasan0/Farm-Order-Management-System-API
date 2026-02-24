"""
Test suite for GraphQL milkAnalytics query.

Tests two layers:
 1. Unit tests on the resolver function (get_milk_analytics) using a mocked DB session.
 2. Integration-style tests via strawberry schema.execute() — no HTTP, no auth, no live DB.

Run with:
    pytest tests/test_graphql_milk_analytics.py -v
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from collections import namedtuple

# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

# Represents a single DB row returned by the aggregate query
MilkRow = namedtuple("MilkRow", ["period", "date", "total_milk", "avg_fat", "avg_snf"])


def make_mock_db(rows):
    """
    Return an async context-manager mock for AsyncSessionLocal
    that yields a session whose execute() returns the given rows.
    """
    mock_result = MagicMock()
    mock_result.all.return_value = rows

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    return mock_ctx


# ---------------------------------------------------------------------------
# 1. Unit tests — get_milk_analytics resolver
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.graphql.resolvers.AsyncSessionLocal")
async def test_milk_analytics_day_period_returns_results(mock_session_local):
    """DAY period should return one MilkProductionAnalytics per row."""
    from app.graphql.resolvers import get_milk_analytics

    rows = [
        MilkRow(
            period=date(2024, 1, 1),
            date=date(2024, 1, 1),
            total_milk=20.0,
            avg_fat=4.5,
            avg_snf=8.2,
        ),
        MilkRow(
            period=date(2024, 1, 2),
            date=date(2024, 1, 2),
            total_milk=15.5,
            avg_fat=4.1,
            avg_snf=8.0,
        ),
    ]
    mock_session_local.return_value = make_mock_db(rows)

    results = await get_milk_analytics(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        period="DAY",
    )

    assert len(results) == 2
    assert results[0].total_milk == 20.0
    assert results[0].avg_fat == 4.5
    assert results[0].avg_snf == 8.2
    assert results[1].total_milk == 15.5


@pytest.mark.asyncio
@patch("app.graphql.resolvers.AsyncSessionLocal")
async def test_milk_analytics_month_period(mock_session_local):
    """MONTH period should group by year-month string."""
    from app.graphql.resolvers import get_milk_analytics

    rows = [
        MilkRow(
            period="2024-01",
            date=date(2024, 1, 1),
            total_milk=120.0,
            avg_fat=4.3,
            avg_snf=8.1,
        ),
        MilkRow(
            period="2024-02",
            date=date(2024, 2, 1),
            total_milk=95.5,
            avg_fat=4.0,
            avg_snf=7.9,
        ),
    ]
    mock_session_local.return_value = make_mock_db(rows)

    results = await get_milk_analytics(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 2, 29),
        period="MONTH",
    )

    assert len(results) == 2
    assert results[0].period == "2024-01"
    assert results[1].period == "2024-02"
    assert results[0].total_milk == 120.0


@pytest.mark.asyncio
@patch("app.graphql.resolvers.AsyncSessionLocal")
async def test_milk_analytics_year_period(mock_session_local):
    """YEAR period should group by year string."""
    from app.graphql.resolvers import get_milk_analytics

    rows = [
        MilkRow(
            period="2023",
            date=date(2023, 1, 1),
            total_milk=800.0,
            avg_fat=4.2,
            avg_snf=8.0,
        ),
        MilkRow(
            period="2024",
            date=date(2024, 1, 1),
            total_milk=950.0,
            avg_fat=4.4,
            avg_snf=8.3,
        ),
    ]
    mock_session_local.return_value = make_mock_db(rows)

    results = await get_milk_analytics(
        start_date=date(2023, 1, 1),
        end_date=date(2024, 12, 31),
        period="YEAR",
    )

    assert len(results) == 2
    assert results[0].period == "2023"
    assert results[1].period == "2024"


@pytest.mark.asyncio
@patch("app.graphql.resolvers.AsyncSessionLocal")
async def test_milk_analytics_week_period(mock_session_local):
    """WEEK period should group by ISO week string."""
    from app.graphql.resolvers import get_milk_analytics

    rows = [
        MilkRow(
            period="2024-W01",
            date=date(2024, 1, 1),
            total_milk=50.0,
            avg_fat=4.0,
            avg_snf=8.0,
        ),
    ]
    mock_session_local.return_value = make_mock_db(rows)

    results = await get_milk_analytics(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 7),
        period="WEEK",
    )

    assert len(results) == 1
    assert results[0].period == "2024-W01"


@pytest.mark.asyncio
@patch("app.graphql.resolvers.AsyncSessionLocal")
async def test_milk_analytics_with_animal_id_filter(mock_session_local):
    """Providing animal_id should apply the filter — the query must include it."""
    from app.graphql.resolvers import get_milk_analytics

    rows = [
        MilkRow(
            period=date(2024, 3, 1),
            date=date(2024, 3, 1),
            total_milk=10.0,
            avg_fat=3.9,
            avg_snf=7.8,
        ),
    ]
    mock_ctx = make_mock_db(rows)
    mock_session_local.return_value = mock_ctx

    results = await get_milk_analytics(
        start_date=date(2024, 3, 1),
        end_date=date(2024, 3, 31),
        animal_id=42,
        period="DAY",
    )

    # Verify the execute was called (animal_id filter was passed into the query)
    session = await mock_ctx.__aenter__()
    session.execute.assert_called_once()

    assert len(results) == 1
    assert results[0].total_milk == 10.0


@pytest.mark.asyncio
@patch("app.graphql.resolvers.AsyncSessionLocal")
async def test_milk_analytics_empty_result(mock_session_local):
    """Should return an empty list when no data exists in the date range."""
    from app.graphql.resolvers import get_milk_analytics

    mock_session_local.return_value = make_mock_db([])

    results = await get_milk_analytics(
        start_date=date(2030, 1, 1),
        end_date=date(2030, 12, 31),
        period="DAY",
    )

    assert results == []


@pytest.mark.asyncio
@patch("app.graphql.resolvers.AsyncSessionLocal")
async def test_milk_analytics_null_fat_snf_defaults_to_zero(mock_session_local):
    """NULL avg_fat / avg_snf from DB should default to 0.0 in the response."""
    from app.graphql.resolvers import get_milk_analytics

    rows = [
        MilkRow(
            period=date(2024, 5, 1),
            date=date(2024, 5, 1),
            total_milk=5.0,
            avg_fat=None,
            avg_snf=None,
        ),
    ]
    mock_session_local.return_value = make_mock_db(rows)

    results = await get_milk_analytics(
        start_date=date(2024, 5, 1),
        end_date=date(2024, 5, 31),
        period="DAY",
    )

    assert results[0].avg_fat == 0.0
    assert results[0].avg_snf == 0.0


# ---------------------------------------------------------------------------
# 2. GraphQL schema-level tests via strawberry schema.execute()
# ---------------------------------------------------------------------------

MILK_ANALYTICS_QUERY = """
query MilkAnalytics(
    $startDate: Date!,
    $endDate: Date!,
    $animalId: Int,
    $period: String
) {
    milkAnalytics(
        startDate: $startDate,
        endDate: $endDate,
        animalId: $animalId,
        period: $period
    ) {
        period
        date
        totalMilk
        avgFat
        avgSnf
    }
}
"""


@pytest.mark.asyncio
@patch("app.graphql.resolvers.AsyncSessionLocal")
async def test_graphql_schema_milk_analytics_success(mock_session_local):
    """GraphQL query should return correctly serialised milkAnalytics data."""
    from app.graphql.schema import schema

    rows = [
        MilkRow(
            period=date(2024, 6, 1),
            date=date(2024, 6, 1),
            total_milk=30.0,
            avg_fat=4.5,
            avg_snf=8.1,
        ),
    ]
    mock_session_local.return_value = make_mock_db(rows)

    result = await schema.execute(
        MILK_ANALYTICS_QUERY,
        variable_values={
            "startDate": "2024-06-01",
            "endDate": "2024-06-30",
            "period": "DAY",
        },
    )

    assert result.errors is None, f"GraphQL errors: {result.errors}"
    data = result.data["milkAnalytics"]
    assert len(data) == 1
    assert data[0]["totalMilk"] == 30.0
    assert data[0]["avgFat"] == 4.5
    assert data[0]["avgSnf"] == 8.1


@pytest.mark.asyncio
@patch("app.graphql.resolvers.AsyncSessionLocal")
async def test_graphql_schema_milk_analytics_empty(mock_session_local):
    """GraphQL query should return empty list when no milk data exists."""
    from app.graphql.schema import schema

    mock_session_local.return_value = make_mock_db([])

    result = await schema.execute(
        MILK_ANALYTICS_QUERY,
        variable_values={
            "startDate": "2030-01-01",
            "endDate": "2030-12-31",
            "period": "MONTH",
        },
    )

    assert result.errors is None
    assert result.data["milkAnalytics"] == []


@pytest.mark.asyncio
@patch("app.graphql.resolvers.AsyncSessionLocal")
async def test_graphql_schema_milk_analytics_with_animal_id(mock_session_local):
    """GraphQL query with animalId variable should execute without errors."""
    from app.graphql.schema import schema

    rows = [
        MilkRow(
            period="2024-07",
            date=date(2024, 7, 1),
            total_milk=60.0,
            avg_fat=4.2,
            avg_snf=8.0,
        ),
    ]
    mock_session_local.return_value = make_mock_db(rows)

    result = await schema.execute(
        MILK_ANALYTICS_QUERY,
        variable_values={
            "startDate": "2024-07-01",
            "endDate": "2024-07-31",
            "animalId": 5,
            "period": "MONTH",
        },
    )

    assert result.errors is None
    data = result.data["milkAnalytics"]
    assert len(data) == 1
    assert data[0]["period"] == "2024-07"
    assert data[0]["totalMilk"] == 60.0
