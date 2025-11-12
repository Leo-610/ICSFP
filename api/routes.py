"""
API Routes for iCast Platform
"""

from flask import Blueprint, jsonify, request, current_app
import numpy as np
import torch
import logging
from typing import Dict, List, Any

from api.schemas import (
    PredictionRequest, 
    BatchPredictionRequest,
    CausalGraphRequest,
    validate_request
)

logger = logging.getLogger(__name__)

# 使用增强版 predictor.py (已集成 predictor_enhanced 的功能)
from api.predictor import StockPredictor

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# 全局预测器实例（延迟加载）
_predictor = None


def get_predictor():
    """获取预测器实例（单例模式）"""
    global _predictor
    if _predictor is None:
        config_path = current_app.config.get('CONFIG_PATH', 'config.yml')
        _predictor = StockPredictor(config_path)
    return _predictor


@api_bp.route('/predict/single', methods=['POST'])
def predict_single_stock():
    """
    单只股票预测接口
    
    Request Body:
    {
        "stock_symbol": "AAPL",
        "start_date": "2015-10-01",
        "end_date": "2015-10-05",
        "use_causal": true
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "stock_symbol": "AAPL",
            "predictions": [
                {
                    "date": "2015-10-01",
                    "predicted_direction": "UP",
                    "confidence": 0.85,
                    "probabilities": {"UP": 0.85, "DOWN": 0.15}
                }
            ]
        }
    }
    """
    try:
        # 验证请求
        data = request.get_json()
        errors = validate_request(data, PredictionRequest)
        if errors:
            return jsonify({'status': 'error', 'message': 'Invalid request', 'errors': errors}), 400
        
        # 获取参数
        stock_symbol = data['stock_symbol']
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        use_causal = data.get('use_causal', True)
        
        # 执行预测
        predictor = get_predictor()
        result = predictor.predict_single(
            stock_symbol=stock_symbol,
            start_date=start_date,
            end_date=end_date,
            use_causal=use_causal
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@api_bp.route('/predict/batch', methods=['POST'])
def predict_batch():
    """
    批量股票预测接口
    
    Request Body:
    {
        "stock_symbols": ["AAPL", "GOOG", "MSFT"],
        "start_date": "2015-10-01",
        "end_date": "2015-10-05",
        "use_causal": true
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "predictions": {
                "AAPL": [...],
                "GOOG": [...],
                "MSFT": [...]
            },
            "summary": {
                "total_stocks": 3,
                "total_predictions": 15,
                "avg_confidence": 0.78
            }
        }
    }
    """
    try:
        # 验证请求
        data = request.get_json()
        errors = validate_request(data, BatchPredictionRequest)
        if errors:
            return jsonify({'status': 'error', 'message': 'Invalid request', 'errors': errors}), 400
        
        # 获取参数
        stock_symbols = data['stock_symbols']
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        use_causal = data.get('use_causal', True)
        
        # 执行批量预测
        predictor = get_predictor()
        result = predictor.predict_batch(
            stock_symbols=stock_symbols,
            start_date=start_date,
            end_date=end_date,
            use_causal=use_causal
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Batch prediction error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@api_bp.route('/causal/graph', methods=['GET'])
def get_causal_graph():
    """
    获取因果图接口
    
    Query Parameters:
    - stocks: 逗号分隔的股票代码列表（可选）
    - threshold: 因果关系阈值（可选，默认0.3）
    
    Response:
    {
        "status": "success",
        "data": {
            "graph": [[0.0, 0.5, ...], ...],
            "stocks": ["AAPL", "GOOG", ...],
            "edges": [
                {"from": "AAPL", "to": "GOOG", "weight": 0.5}
            ]
        }
    }
    """
    try:
        # 获取参数
        stocks_str = request.args.get('stocks')
        threshold = float(request.args.get('threshold', 0.3))
        
        stocks = stocks_str.split(',') if stocks_str else None
        
        # 获取因果图
        predictor = get_predictor()
        result = predictor.get_causal_graph(stocks=stocks, threshold=threshold)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Causal graph error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@api_bp.route('/causal/influence', methods=['GET'])
def get_causal_influence():
    """
    获取股票的因果影响力分析
    
    Query Parameters:
    - stock: 股票代码
    - top_k: 返回前k个影响最大的股票（默认10）
    
    Response:
    {
        "status": "success",
        "data": {
            "stock": "AAPL",
            "influenced_by": [
                {"stock": "GOOG", "weight": 0.8},
                {"stock": "MSFT", "weight": 0.6}
            ],
            "influences": [
                {"stock": "TSLA", "weight": 0.7}
            ]
        }
    }
    """
    try:
        stock = request.args.get('stock')
        if not stock:
            return jsonify({'status': 'error', 'message': 'Stock symbol is required'}), 400
        
        top_k = int(request.args.get('top_k', 10))
        
        # 获取因果影响分析
        predictor = get_predictor()
        result = predictor.get_causal_influence(stock=stock, top_k=top_k)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Causal influence error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@api_bp.route('/stocks', methods=['GET'])
def get_available_stocks():
    """
    获取可用股票列表
    
    Query Parameters:
    - sector: 板块过滤（可选）
    
    Response:
    {
        "status": "success",
        "data": {
            "stocks": ["AAPL", "GOOG", ...],
            "sectors": {
                "tech": ["AAPL", "GOOG", ...],
                "finance": [...]
            }
        }
    }
    """
    try:
        sector = request.args.get('sector')
        
        predictor = get_predictor()
        result = predictor.get_available_stocks(sector=sector)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Get stocks error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@api_bp.route('/model/info', methods=['GET'])
def get_model_info():
    """
    获取模型信息
    
    Response:
    {
        "status": "success",
        "data": {
            "model_name": "...",
            "parameters": 1234567,
            "device": "cuda",
            "config": {...}
        }
    }
    """
    try:
        predictor = get_predictor()
        result = predictor.get_model_info()
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Get model info error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


def register_routes(app):
    """注册所有路由到应用"""
    app.register_blueprint(api_bp)
    logger.info('API routes registered successfully')
