"""OpenFlow API 主客户端

提供与 OpenFlow API 交互的高层接口，支持自动重试、错误处理和日志记录。
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from openflow_client.auth import AuthHandler, create_auth
from openflow_client.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    RateLimitError,
)
from openflow_client.models import Workflow, WorkflowRun

logger = logging.getLogger(__name__)


class OpenFlowClient:
    """OpenFlow API 客户端

    使用示例:
        >>> client = OpenFlowClient.from_env()
        >>> workflows = client.list_workflows()
        >>> print(workflows)
    """

    def __init__(
        self,
        base_url: str,
        auth: AuthHandler,
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True,
    ):
        if not base_url:
            raise ConfigurationError("base_url 不能为空")

        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl

        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @classmethod
    def from_env(cls) -> OpenFlowClient:
        """从环境变量创建客户端

        必需的环境变量：
            OPENFLOW_API_KEY: API 密钥
            OPENFLOW_API_URL: API 基础 URL

        可选的环境变量：
            OPENFLOW_TIMEOUT: 请求超时（默认 30）
            OPENFLOW_MAX_RETRIES: 最大重试次数（默认 3）
        """
        api_key = os.getenv("OPENFLOW_API_KEY")
        base_url = os.getenv("OPENFLOW_API_URL")

        if not api_key:
            raise ConfigurationError(
                "缺少 OPENFLOW_API_KEY 环境变量。请在 .env 文件中配置或导出该变量。"
            )
        if not base_url:
            raise ConfigurationError(
                "缺少 OPENFLOW_API_URL 环境变量。请在 .env 文件中配置或导出该变量。"
            )

        return cls(
            base_url=base_url,
            auth=create_auth("api_key", api_key=api_key),
            timeout=int(os.getenv("OPENFLOW_TIMEOUT", "30")),
            max_retries=int(os.getenv("OPENFLOW_MAX_RETRIES", "3")),
        )

    def _build_headers(self) -> dict:
        """构建请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "openflow-python-client/0.1.0",
        }
        return self.auth.apply(headers)

    def _handle_response(self, response: requests.Response) -> dict:
        """处理 HTTP 响应，把错误转换为对应异常"""
        if response.status_code == 401:
            raise AuthenticationError(
                "认证失败：API Key 无效或已过期",
                status_code=401,
                response_body=response.text,
            )
        if response.status_code == 403:
            raise AuthenticationError(
                "权限不足：当前 API Key 无权访问该资源",
                status_code=403,
                response_body=response.text,
            )
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                "请求频率超限",
                retry_after=int(retry_after) if retry_after else None,
                status_code=429,
                response_body=response.text,
            )
        if response.status_code >= 400:
            raise APIError(
                f"API 请求失败: {response.reason}",
                status_code=response.status_code,
                response_body=response.text,
            )

        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as e:
            raise APIError(
                f"响应解析失败，不是有效的 JSON: {e}",
                status_code=response.status_code,
                response_body=response.text,
            ) from e

    @retry(
        retry=retry_if_exception_type((NetworkError, RateLimitError)),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _request(self, method: str, path: str, **kwargs) -> dict:
        """发送 HTTP 请求（带自动重试）

        Args:
            method: HTTP 方法 (GET/POST/PUT/DELETE)
            path: API 路径（相对 base_url）
            **kwargs: 透传给 requests 的额外参数

        Returns:
            响应 JSON 解析后的字典

        Raises:
            AuthenticationError: 认证失败
            RateLimitError: 频率限制
            APIError: 其它 API 错误
            NetworkError: 网络错误
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = self._build_headers()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        logger.debug("发送请求: %s %s", method, url)

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs,
            )
        except requests.Timeout as e:
            raise NetworkError(f"请求超时（{self.timeout}s）: {url}") from e
        except requests.ConnectionError as e:
            raise NetworkError(f"网络连接失败: {e}") from e
        except requests.RequestException as e:
            raise NetworkError(f"请求异常: {e}") from e

        return self._handle_response(response)

    def health_check(self) -> bool:
        """健康检查：测试 API 是否可访问

        Returns:
            True 如果 API 正常响应
        """
        try:
            self._request("GET", "/health")
            return True
        except Exception as e:
            logger.warning("健康检查失败: %s", e)
            return False

    def list_workflows(self, limit: int = 100, offset: int = 0) -> list[Workflow]:
        """列出所有工作流"""
        data = self._request("GET", "/workflows", params={"limit": limit, "offset": offset})
        return [Workflow(**item) for item in data.get("items", [])]

    def get_workflow(self, workflow_id: str) -> Workflow:
        """获取指定工作流详情"""
        data = self._request("GET", f"/workflows/{workflow_id}")
        return Workflow(**data)

    def create_workflow(self, name: str, description: str = "", config: dict | None = None) -> Workflow:
        """创建新工作流"""
        payload: dict[str, Any] = {"name": name, "description": description}
        if config:
            payload["config"] = config
        data = self._request("POST", "/workflows", json=payload)
        return Workflow(**data)

    def delete_workflow(self, workflow_id: str) -> None:
        """删除工作流"""
        self._request("DELETE", f"/workflows/{workflow_id}")

    def run_workflow(self, workflow_id: str, input_data: dict | None = None) -> WorkflowRun:
        """触发工作流执行"""
        payload = {"input": input_data or {}}
        data = self._request("POST", f"/workflows/{workflow_id}/runs", json=payload)
        return WorkflowRun(**data)

    def get_run(self, run_id: str) -> WorkflowRun:
        """查询工作流执行状态"""
        data = self._request("GET", f"/runs/{run_id}")
        return WorkflowRun(**data)

    def close(self) -> None:
        """关闭 HTTP 会话"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()
