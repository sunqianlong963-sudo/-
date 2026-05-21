"""OpenFlow API 客户端

提供与 OpenFlow API 交互的高层封装，包括认证、自动重试、错误处理等功能。
"""

from openflow_client.client import OpenFlowClient
from openflow_client.exceptions import (
    OpenFlowError,
    AuthenticationError,
    APIError,
    RateLimitError,
    NetworkError,
)
from openflow_client.models import Workflow, WorkflowRun, ApiResponse

__version__ = "0.1.0"

__all__ = [
    "OpenFlowClient",
    "OpenFlowError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
    "NetworkError",
    "Workflow",
    "WorkflowRun",
    "ApiResponse",
]
