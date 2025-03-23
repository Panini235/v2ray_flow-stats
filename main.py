import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import setup_logger
from core.flow import flow_manager

logger = setup_logger(__name__)

def main():

    try:
        logger.info("=== 开始执行流量统计更新 ===")
        stat = flow_manager.query_flow()

        flow_data = flow_manager.format_flow_data(stat)

        flow_manager.update_flow_stats(flow_data)

        flow_manager.reset_flow()

        logger.info("=== 流量统计完成 ===")
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()