import os, sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger
from typing import Dict, List
from database.dynamodb import db_client

logger = setup_logger(__name__)

class FlowManager:

    @staticmethod
    def query_flow() -> dict:

        try:
            command = "/usr/local/bin/v2ray api stats -s 127.0.0.1:10085 -json"
            logger.info(f"执行命令: {command}")
            result = os.popen(command)
            stat = json.loads(result.read())["stat"]
            logger.info(f"成功获取流量数据，共 {len(stat)} 条记录")
            return stat
        except Exception as e:
            logger.error(f"获取流量统计失败: {str(e)}")
            raise

    @staticmethod
    def format_flow_data(stat: List[Dict]) -> Dict[str, Dict[str, str]]:
        flow_data = {}
        for item in stat:
            if "value" not in item:
                continue
            data = item["name"].split(">>>")
            username = data[1]
            flow_type = data[3]
            flow_value = item["value"]
            flow_data.setdefault(username, {})
            flow_data[username][flow_type] = flow_value
        return flow_data

    @staticmethod
    def update_flow_stats(flow_data: Dict[str, Dict[str, str]]):
        try:
            for username, data in flow_data.items():
                upload = data["uplink"]
                download = data["downlink"]
                db_client.update_user_flow(username=username, upload=upload, download=download)
        except Exception as e:
            logger.error(f"流量更新时失败，{str(e)}")
            raise


    @staticmethod
    def reset_flow():
        """重置V2Ray的流量统计数据"""
        try:
            logger.info("开始重置流量统计...")
            command = f"v2ray api stats -s 127.0.0.1:10085 -reset"
            os.popen(command)
            logger.info("流量统计重置成功")
        except Exception as e:
            logger.error(f"重置流量统计失败: {str(e)}")
            raise

flow_manager = FlowManager()

