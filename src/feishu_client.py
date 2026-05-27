"""飞书多维表格客户端（仅依赖 httpx，不引入 lark SDK）。

文档：
- 鉴权：https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
- 多维表格新增记录：https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/create
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

BASE = "https://open.feishu.cn/open-apis"


class FeishuClient:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token: str | None = None
        self._token_expire: float = 0.0
        self._http = httpx.Client(timeout=30.0)

    def _tenant_token(self) -> str:
        if self._token and time.time() < self._token_expire - 60:
            return self._token
        r = self._http.post(
            f"{BASE}/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
        )
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"飞书鉴权失败: {data}")
        self._token = data["tenant_access_token"]
        self._token_expire = time.time() + data.get("expire", 7200)
        return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._tenant_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def create_record(self, app_token: str, table_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        url = f"{BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        r = self._http.post(url, headers=self._headers(), json={"fields": fields})
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"飞书写入失败: {data}")
        return data["data"]["record"]

    def batch_create(self, app_token: str, table_id: str, records: list[dict[str, Any]]) -> int:
        """批量写入（接口单次最多 1000 条，按 100 一批分片）。"""
        url = f"{BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        total = 0
        for i in range(0, len(records), 100):
            chunk = [{"fields": f} for f in records[i:i + 100]]
            r = self._http.post(url, headers=self._headers(), json={"records": chunk})
            r.raise_for_status()
            data = r.json()
            if data.get("code") != 0:
                raise RuntimeError(f"飞书批量写入失败: {data}")
            total += len(chunk)
        return total
