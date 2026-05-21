"""OpenFlow 客户端基础用法示例

运行前请确保：
1. 已安装依赖：pip install -r requirements.txt
2. 已配置 .env 文件（参考 .env.example）
"""

import logging
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，便于直接运行示例
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from openflow_client import (
    AuthenticationError,
    NetworkError,
    OpenFlowClient,
    OpenFlowError,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("example")


def main() -> int:
    # 加载 .env 文件中的环境变量
    load_dotenv()

    try:
        # 通过环境变量初始化客户端
        with OpenFlowClient.from_env() as client:
            logger.info("OpenFlow 客户端已初始化")
            logger.info("API URL: %s", client.base_url)

            # 步骤 1: 健康检查
            logger.info("正在进行健康检查...")
            if not client.health_check():
                logger.error("❌ 健康检查失败，请检查 API 地址与网络")
                return 1
            logger.info("✅ API 可访问")

            # 步骤 2: 列出工作流
            logger.info("正在获取工作流列表...")
            workflows = client.list_workflows(limit=10)
            logger.info("找到 %d 个工作流", len(workflows))
            for wf in workflows:
                logger.info("  - [%s] %s (状态: %s)", wf.id, wf.name, wf.status)

        return 0

    except AuthenticationError as e:
        logger.error("❌ 认证失败: %s", e)
        logger.error("请检查 OPENFLOW_API_KEY 是否正确")
        return 2
    except NetworkError as e:
        logger.error("❌ 网络错误: %s", e)
        logger.error("请检查 OPENFLOW_API_URL 与网络连通性")
        return 3
    except OpenFlowError as e:
        logger.error("❌ API 错误: %s", e)
        if e.response_body:
            logger.error("响应内容: %s", e.response_body[:500])
        return 4


if __name__ == "__main__":
    sys.exit(main())
