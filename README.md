# OpenFlow API 集成项目

这是一个完整的 OpenFlow API 客户端集成示例，提供了从配置、认证到 API 调用的完整方案。

## 项目结构

```
.
├── openflow_client/      # OpenFlow API 客户端核心代码
│   ├── __init__.py
│   ├── client.py         # 主客户端类
│   ├── auth.py           # 认证模块
│   ├── exceptions.py     # 自定义异常
│   └── models.py         # 数据模型
├── config/               # 配置文件目录
│   ├── config.example.yaml
│   └── config.yaml       # （需自行创建，不要提交）
├── examples/             # 使用示例
│   ├── basic_usage.py
│   ├── create_workflow.py
│   └── list_workflows.py
├── tests/                # 测试代码
│   └── test_client.py
├── requirements.txt      # Python 依赖
└── .env.example          # 环境变量示例
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

复制配置文件示例：

```bash
cp config/config.example.yaml config/config.yaml
cp .env.example .env
```

然后编辑 `.env` 文件，填入你的 API 密钥：

```env
OPENFLOW_API_KEY=your_api_key_here
OPENFLOW_API_URL=https://api.openflow.example.com/v1
```

### 3. 运行示例

```bash
python examples/basic_usage.py
```

## 常见 API 接入问题

### 问题 1：连接超时
- **原因**：网络问题或 API 服务地址错误
- **解决**：检查 `OPENFLOW_API_URL` 配置；测试 `ping` 或 `curl` 能否访问

### 问题 2：401 认证失败
- **原因**：API Key 错误、过期或权限不足
- **解决**：检查 API Key 是否正确；确认 token 没有过期

### 问题 3：429 频率限制
- **原因**：调用频率过高
- **解决**：客户端已内置指数退避重试机制；可调整 `retry_delay` 配置

### 问题 4：SSL 证书错误
- **原因**：自签名证书或证书过期
- **解决**：在配置中设置 `verify_ssl: false`（仅测试环境使用）

## 详细文档

查看 `examples/` 目录中的示例代码了解具体用法。
