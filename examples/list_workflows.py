"""列出工作流的示例（带分页）"""

import logging
import sys
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
            offset = 0
            page_size = 20
            total = 0

            while True:
                workflows = client.list_workflows(limit=page_size, offset=offset)
                if not workflows:
                    break

                for wf in workflows:
                    total += 1
                    print(f"{total:>3}. [{wf.status:>10}] {wf.name}  (id={wf.id})")

                if len(workflows) < page_size:
                    break
                offset += page_size

            logger.info("共找到 %d 个工作流", total)
        return 0
    except OpenFlowError as e:
        logger.error("❌ 失败: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
