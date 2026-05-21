"""OpenFlow 客户端的自定义异常类"""


class OpenFlowError(Exception):
    """OpenFlow 客户端的基础异常类"""

    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(OpenFlowError):
    """认证失败异常 (HTTP 401/403)"""


class APIError(OpenFlowError):
    """通用 API 错误异常 (HTTP 4xx/5xx)"""


class RateLimitError(OpenFlowError):
    """请求频率超限异常 (HTTP 429)"""

    def __init__(self, message: str, retry_after: int | None = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class NetworkError(OpenFlowError):
    """网络连接异常（超时、DNS 失败等）"""


class ConfigurationError(OpenFlowError):
    """配置错误异常"""
