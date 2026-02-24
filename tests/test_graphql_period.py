import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_period_queries():
    print("Testing Milk Production (DAY)...")
    response = client.post(
        "/graphql",
        json={
            "query": """
            query {
                milkAnalytics(startDate: "2023-01-01", endDate: "2025-12-31", period: "DAY") {
                    period
                    date
                    totalMilk
                }
            }
        """
        },
    )
    print(response.json())
    assert response.status_code == 200

    print("\nTesting Milk Production (MONTH)...")
    response = client.post(
        "/graphql",
        json={
            "query": """
            query {
                milkAnalytics(startDate: "2023-01-01", endDate: "2025-12-31", period: "MONTH") {
                    period
                    totalMilk
                
                }
            }
        """
        },
    )
    print(response.json())
    assert response.status_code == 200

    print("\nTesting Milk Production (YEAR)...")
    response = client.post(
        "/graphql",
        json={
            "query": """
            query {
                milkAnalytics(startDate: "2023-01-01", endDate: "2025-12-31", period: "YEAR") {
                    period
                    totalMilk
                }
            }
        """
        },
    )
    print(response.json())
    assert response.status_code == 200


if __name__ == "__main__":
    test_period_queries()
