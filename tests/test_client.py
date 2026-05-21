"""OpenFlow 客户端单元测试

运行: pytest tests/
"""

import pytest
from unittest.mock import MagicMock, patch

from openflow_client import (
    APIError,
    AuthenticationError,
    OpenFlowClient,
    RateLimitError,
)
from openflow_client.auth import ApiKeyAuth, BearerTokenAuth, create_auth


@pytest.fixture
def client():
    return OpenFlowClient(
        base_url="https://api.test.com/v1",
        auth=ApiKeyAuth(api_key="test_key"),
        timeout=10,
        max_retries=2,
    )


def test_api_key_auth_applies_header():
    auth = ApiKeyAuth(api_key="abc123")
    headers = auth.apply({})
    assert headers["X-API-Key"] == "abc123"


def test_api_key_auth_custom_header():
    auth = ApiKeyAuth(api_key="abc123", header_name="Authorization")
    headers = auth.apply({})
    assert headers["Authorization"] == "abc123"


def test_api_key_auth_rejects_empty():
    with pytest.raises(ValueError):
        ApiKeyAuth(api_key="")


def test_bearer_token_auth():
    auth = BearerTokenAuth(token="xyz789")
    headers = auth.apply({})
    assert headers["Authorization"] == "Bearer xyz789"


def test_create_auth_factory():
    auth = create_auth("api_key", api_key="k")
    assert isinstance(auth, ApiKeyAuth)

    auth = create_auth("bearer_token", token="t")
    assert isinstance(auth, BearerTokenAuth)

    with pytest.raises(ValueError):
        create_auth("unknown_type", token="t")


def test_client_strips_trailing_slash():
    c = OpenFlowClient(
        base_url="https://api.test.com/v1/",
        auth=ApiKeyAuth(api_key="k"),
    )
    assert c.base_url == "https://api.test.com/v1"


def test_handle_response_401(client):
    response = MagicMock()
    response.status_code = 401
    response.text = "Unauthorized"
    with pytest.raises(AuthenticationError) as exc_info:
        client._handle_response(response)
    assert exc_info.value.status_code == 401


def test_handle_response_429(client):
    response = MagicMock()
    response.status_code = 429
    response.headers = {"Retry-After": "30"}
    response.text = "Too Many Requests"
    with pytest.raises(RateLimitError) as exc_info:
        client._handle_response(response)
    assert exc_info.value.retry_after == 30


def test_handle_response_500(client):
    response = MagicMock()
    response.status_code = 500
    response.reason = "Internal Server Error"
    response.text = "boom"
    with pytest.raises(APIError):
        client._handle_response(response)


def test_handle_response_success(client):
    response = MagicMock()
    response.status_code = 200
    response.content = b'{"ok": true}'
    response.json.return_value = {"ok": True}
    assert client._handle_response(response) == {"ok": True}


@patch("openflow_client.client.requests.Session.request")
def test_list_workflows_success(mock_request, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"items": []}'
    mock_response.json.return_value = {"items": []}
    mock_request.return_value = mock_response

    result = client.list_workflows()
    assert result == []
    mock_request.assert_called_once()


@patch("openflow_client.client.requests.Session.request")
def test_create_workflow(mock_request, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"id": "w1", "name": "test"}'
    mock_response.json.return_value = {"id": "w1", "name": "test"}
    mock_request.return_value = mock_response

    workflow = client.create_workflow(name="test")
    assert workflow.id == "w1"
    assert workflow.name == "test"
