"""
元数据序列化/反序列化工具

向量数据库 (ChromaDB) 的元数据值只能是标量类型 (str/int/float/bool)，
因此列表/字典字段在写入时会被序列化为 JSON 字符串。读取后需要反序列化
还原为 Python 对象，供下游的过滤、评分、分析等模块使用。

本模块提供统一的序列化/反序列化逻辑，避免各模块各自处理导致的不一致。
"""
import json
from typing import Any, Dict, List


def serialize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    将元数据处理为符合向量数据库要求的格式（标量值）。

    列表/字典 -> JSON 字符串；None -> 空字符串；其他保持原样。

    Args:
        metadata (Dict[str, Any]): 原始元数据

    Returns:
        Dict[str, Any]: 处理后的元数据
    """
    processed: Dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, (list, dict)):
            processed[key] = json.dumps(value, ensure_ascii=False)
        elif value is not None:
            processed[key] = value
        else:
            processed[key] = ""

    # ChromaDB 不接受空元数据
    if not processed:
        processed["default"] = "default_value"

    return processed


def deserialize_value(value: Any) -> Any:
    """
    尝试将单个值反序列化。如果是形如 JSON 数组/对象的字符串则解析为
    list/dict，否则原样返回。
    """
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("[", "{")):
            try:
                return json.loads(stripped)
            except (json.JSONDecodeError, ValueError):
                return value
    return value


def deserialize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    将从向量数据库读取的元数据还原为 Python 对象。

    Args:
        metadata (Dict[str, Any]): 存储格式的元数据

    Returns:
        Dict[str, Any]: 还原后的元数据
    """
    if not isinstance(metadata, dict):
        return metadata
    return {key: deserialize_value(value) for key, value in metadata.items()}


def coerce_to_list(value: Any) -> List[Any]:
    """
    将一个字段稳健地转换为列表，兼容以下输入：
    - 已是 list：直接返回
    - JSON 数组/对象字符串：解析后返回
    - 逗号分隔字符串：按逗号拆分
    - 其他非空标量：包装为单元素列表
    - None / 空字符串：返回空列表
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith(("[", "{")):
            try:
                parsed = json.loads(stripped)
                return parsed if isinstance(parsed, list) else [parsed]
            except (json.JSONDecodeError, ValueError):
                pass
        if "," in stripped:
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return [stripped]
    if value is None:
        return []
    return [value]
