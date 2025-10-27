"""
API Request/Response Schemas
数据验证模式
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class PredictionRequest:
    """单只股票预测请求"""
    required_fields = ['stock_symbol']
    optional_fields = {
        'start_date': str,
        'end_date': str,
        'use_causal': bool
    }


class BatchPredictionRequest:
    """批量股票预测请求"""
    required_fields = ['stock_symbols']
    optional_fields = {
        'start_date': str,
        'end_date': str,
        'use_causal': bool
    }


class CausalGraphRequest:
    """因果图请求"""
    required_fields = []
    optional_fields = {
        'stocks': list,
        'threshold': float
    }


def validate_request(data: Dict[str, Any], schema) -> List[str]:
    """
    验证请求数据
    
    Args:
        data: 请求数据字典
        schema: 验证模式类
    
    Returns:
        错误列表（如果为空则验证通过）
    """
    errors = []
    
    # 检查必需字段
    for field in schema.required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # 检查可选字段类型
    for field, field_type in schema.optional_fields.items():
        if field in data and data[field] is not None:
            if not isinstance(data[field], field_type):
                errors.append(f"Field '{field}' must be of type {field_type.__name__}")
    
    # 特殊验证
    if hasattr(schema, 'required_fields') and 'stock_symbols' in schema.required_fields:
        if 'stock_symbols' in data and len(data['stock_symbols']) == 0:
            errors.append("stock_symbols cannot be empty")
    
    return errors


def format_prediction_response(predictions: List[Dict]) -> Dict[str, Any]:
    """格式化预测响应"""
    return {
        'predictions': predictions,
        'count': len(predictions)
    }


def format_causal_graph_response(graph: Any, stocks: List[str], threshold: float = 0.3) -> Dict[str, Any]:
    """格式化因果图响应"""
    import numpy as np
    
    # 转换图为列表格式
    if hasattr(graph, 'tolist'):
        graph_list = graph.tolist()
    else:
        graph_list = graph
    
    # 提取边
    edges = []
    for i, from_stock in enumerate(stocks):
        for j, to_stock in enumerate(stocks):
            if i != j and graph_list[i][j] > threshold:
                edges.append({
                    'from': from_stock,
                    'to': to_stock,
                    'weight': float(graph_list[i][j])
                })
    
    return {
        'graph': graph_list,
        'stocks': stocks,
        'edges': edges,
        'threshold': threshold
    }
