import falcon.testing
import pytest
from app import api


@pytest.fixture
def client():
    return falcon.testing.TestClient(api)


def test_predict_api(client: falcon.testing.TestClient):
    response = client.simulate_post("/predict", json={"text": "hello world"})
    assert response.status_code == 200
    assert isinstance(response.json["score"], float)
    assert 0 <= response.json["score"] <= 1
