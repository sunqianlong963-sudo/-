"""创建并运行工作流的示例"""

import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from openflow_client import OpenFlowClient, OpenFlowError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("example")


def main() -> int:
    load_dotenv()

    try:
        with OpenFlowClient.from_env() as client:
            # 创建工作流
            logger.info("创建新工作流...")
            workflow = client.create_workflow(
                name="数据处理示例",
                description="一个简单的演示工作流",
                config={
                    "steps": [
                        {"type": "fetch", "url": "https://example.com/data"},
                        {"type": "transform", "operation": "uppercase"},
                        {"type": "save", "destination": "output.json"},
                    ]
                },
            )
            logger.info("✅ 已创建工作流: %s (ID: %s)", workflow.name, workflow.id)

            # 触发执行
            logger.info("触发工作流执行...")
            run = client.run_workflow(workflow.id, input_data={"foo": "bar"})
            logger.info("✅ 已启动执行: run_id=%s, 状态=%s", run.id, run.status)

            # 轮询状态（最多等待 60 秒）
            logger.info("等待执行完成...")
            for _ in range(30):
                time.sleep(2)
                run = client.get_run(run.id)
                logger.info("当前状态: %s", run.status)
                if run.status in ("succeeded", "failed", "cancelled"):
                    break

            if run.status == "succeeded":
                logger.info("✅ 执行成功，输出: %s", run.output_data)
            else:
                logger.warning("⚠️ 执行未成功: %s, 错误: %s", run.status, run.error)

        return 0
    except OpenFlowError as e:
        logger.error("❌ 失败: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
