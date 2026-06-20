"""
数据模型占位符
"""
from pydantic import BaseModel

class PlaceholderModel(BaseModel):
    """
    一个占位符 Pydantic 模型。
    """
    name: str
    value: int