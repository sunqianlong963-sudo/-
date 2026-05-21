"""OpenFlow API 数据模型

使用 Pydantic 进行数据校验和序列化。
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """通用 API 响应"""

    success: bool = True
    data: Any = None
    message: str | None = None
    request_id: str | None = None


class Workflow(BaseModel):
    """工作流定义"""

    id: str
    name: str
    description: str | None = None
    status: str = "draft"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    config: dict = Field(default_factory=dict)


class WorkflowRun(BaseModel):
    """工作流执行实例"""

    id: str
    workflow_id: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    input_data: dict = Field(default_factory=dict)
    output_data: dict = Field(default_factory=dict)
    error: str | None = None


class CreateWorkflowRequest(BaseModel):
    """创建工作流请求"""

    name: str
    description: str | None = None
    config: dict = Field(default_factory=dict)
