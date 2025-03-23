import os
import json
import boto3
import logging
from datetime import datetime
from boto3.dynamodb.conditions import Key

# 配置日志输出格式和保存位置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'/var/log/v2ray/flow_stats_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def read_params_from_os_env():
    """
    从环境变量中读取参数，在Linux中可以使用以下命令实现
    export CONFIG_PATH="/usr/local/etc/v2ray/config.json"
    export REGION="us-east-1"
    export ACCESS_TOKEN="你的aws_access_key"
    export SECRET_ACCESS_KEY="你的secret_acess_key"
    export TABLE_NAME="<Dynamodb表名>"
    export INDEX_NAME="<Dynamodb二级索引名称(主键为username)>"
    """
    try:
        config_path = os.environ.get("CONFIG_PATH")
        region = os.environ.get("REGION")
        # access_key = os.environ.get("ACCESS_TOKEN")
        # secret_access_key = os.environ.get("SECRET_ACCESS_KEY")
        table_name = os.environ.get("TABLE_NAME")
        index_name = os.environ.get("INDEX_NAME")
        env_params = {
            "config_path": config_path,
            "region": region,
            # "access_key": access_key,
            # "secret_access_key": secret_access_key,
            "table_name": table_name,
            "index_name": index_name
        }
        return env_params
    except Exception as e:
        return f"读取环境变量时失败,错误信息: {e}"

def _flow_query():
    """查询 V2Ray 的流量统计数据"""
    try:
        command = "/usr/local/bin/v2ray api stats -s 127.0.0.1:10085 -json"
        result = os.popen(command).read()
        stat = json.loads(result)['stat']
        logger.info(f"成功获取流量统计数据，共 {len(stat)} 条记录")
        return stat
    except Exception as e:
        logger.error(f"目前暂无数据，获取流量统计失败: {str(e)}")
        raise

def _flow_string_format(stat):
    """格式化流量统计数据，按用户名分组统计上下行流量"""
    flow_data = {}
    for item in stat:
        if "value" not in item:
            continue
        data = item['name'].split(">>>")
        username = data[1]
        flow_type = data[3]  # uplink或downlink
        flow_value = int(item['value'])
        flow_data.setdefault(username, {})
        flow_data[username][flow_type] = flow_value
    return flow_data


def reset_flow():
    """重置 V2Ray 的流量统计数据"""
    try:
        logger.info("开始重置流量统计...")
        command = "v2ray api stats -s 127.0.0.1:10085 -reset"
        result = os.popen(command)
        logger.info("流量统计重置成功")
    except Exception as e:
        logger.error(f"重置流量统计失败: {str(e)}")
        raise

def flow_update(data, table_name, region_name, index_name):
    """更新 DynamoDB 中的用户流量数据"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name=region_name)
        table = dynamodb.Table(table_name)
        for username in data:
            # 连接到 DynamoDB
            # 通过用户名查询对应的 UUID
            info = table.query(
                IndexName=index_name,
                KeyConditionExpression=Key('username').eq(username)
            )['Items']
            uuid = info[0]['uuid']
            download = info[0]['download']
            upload = info[0]['upload']
            # 更新用户的流量数据
            response = table.update_item(
                Key={'username': username, 'uuid': uuid},
                UpdateExpression='set upload = :upload, download = :download',
                ExpressionAttributeValues={
                    ':upload': str(int(upload) + data[username]['uplink']),
                    ':download': str(int(download) + data[username]['downlink'])
                }
            )
            logger.info(f"更新流量统计成功: {username}")
    except Exception as e:
        logger.error(f"更新流量统计失败: {str(e)}")
        raise

if __name__ == "__main__":
    # 主程序流程
    logger.info("=== 读取环境变量 ===")
    env_params = read_params_from_os_env()
    logger.info("=== 开始执行流量统计任务 ===")
    stat = _flow_query()  # 获取流量数据
    data = _flow_string_format(stat)  # 格式化数据
    print(data)
    # 更新数据库并重置流量计数
    flow_update(data=data, region_name=env_params["region"], table_name=env_params["table_name"], index_name=env_params["index_name"])
    reset_flow()
    logger.info("=== 日志位置：/var/log/v2ray/ ===")
