"""OpenFlow 认证模块

支持多种认证方式：API Key、Bearer Token、OAuth2
"""

from abc import ABC, abstractmethod


class AuthHandler(ABC):
    """认证处理器基类"""

    @abstractmethod
    def apply(self, headers: dict) -> dict:
        """将认证信息应用到请求头"""
        ...


class ApiKeyAuth(AuthHandler):
    """API Key 认证

    将 API Key 添加到指定的请求头中（默认 X-API-Key）。
    """

    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        if not api_key:
            raise ValueError("API Key 不能为空")
        self.api_key = api_key
        self.header_name = header_name

    def apply(self, headers: dict) -> dict:
        headers[self.header_name] = self.api_key
        return headers


class BearerTokenAuth(AuthHandler):
    """Bearer Token 认证

    将 token 添加到 Authorization 请求头中（格式：Bearer <token>）。
    """

    def __init__(self, token: str):
        if not token:
            raise ValueError("Token 不能为空")
        self.token = token

    def apply(self, headers: dict) -> dict:
        headers["Authorization"] = f"Bearer {self.token}"
        return headers


def create_auth(auth_type: str, **kwargs) -> AuthHandler:
    """根据配置创建对应的认证处理器

    Args:
        auth_type: 认证类型 (api_key | bearer_token)
        **kwargs: 认证参数

    Returns:
        AuthHandler 实例
    """
    auth_type = auth_type.lower()
    if auth_type == "api_key":
        return ApiKeyAuth(
            api_key=kwargs["api_key"],
            header_name=kwargs.get("header_name", "X-API-Key"),
        )
    if auth_type == "bearer_token":
        return BearerTokenAuth(token=kwargs["token"])
    raise ValueError(f"不支持的认证类型: {auth_type}")
