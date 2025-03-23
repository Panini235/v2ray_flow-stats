import boto3
from boto3.dynamodb.conditions import Key
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DynamoDBClient:

    def __init__(self):
        self.dynamodb = boto3.resource(
                            "dynamodb",
                            region_name=settings.region
                        )
        self.table = self.dynamodb.Table(settings.table)

    def get_user_info_by_username(self, username: str) -> dict:
        try:
            response = self.table.query(
                IndexName = settings.index,
                KeyConditionExpression = Key("username").eq(username)
            )
            return response["Items"][0] if response["Items"] else None
        except Exception as e:
            logger.error(f"查询用户{username}失败: {str(e)}")
            raise

    def update_user_flow(self, username: str, upload: str, download: str):
        try:
            current_data = self.get_user_info_by_username(username)
            uuid = current_data["uuid"]
            update_upload = int(current_data["upload"]) + int(upload)
            update_download = int(current_data["download"]) + int(download)
            self.table.update_item(
                Key={"username": username, "uuid": uuid},
                UpdateExpression='set upload = :upload, download = :download',
                ExpressionAttributeValues={
                    ":upload": str(update_upload),
                    ":download": str(update_download)
                }
            )
            logger.info(f"用户{username}流量数据更新成功,当前总量: 上传 {update_upload}, 下载 {update_download}")
        except Exception as e:
            logger.error(f"用户{username}更新流量数据失败,{str(e)}")


db_client = DynamoDBClient()