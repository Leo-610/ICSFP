"""
实时数据API路由
提供实时股票数据查询、订阅和推送功能
"""

from flask import Blueprint, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
from typing import Dict, List
from api.realtime_data import get_realtime_manager

logger = logging.getLogger(__name__)

# 创建蓝图
realtime_bp = Blueprint('realtime', __name__, url_prefix='/api/v1/realtime')

# SocketIO实例（在app.py中初始化）
socketio = None


def init_socketio(app):
    """初始化SocketIO"""
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    logger.info("SocketIO initialized for realtime data")
    return socketio


@realtime_bp.route('/quote/<symbol>', methods=['GET'])
def get_quote(symbol: str):
    """
    获取单只股票实时报价
    
    GET /api/v1/realtime/quote/AAPL
    
    Query Parameters:
    - source: 数据源 (可选: yahoo_finance, alpha_vantage, tushare)
    - use_cache: 是否使用缓存 (默认: true)
    
    Response:
    {
        "status": "success",
        "data": {
            "symbol": "AAPL",
            "price": 150.25,
            "open": 149.50,
            "high": 151.00,
            "low": 149.00,
            "volume": 75000000,
            "previous_close": 149.80,
            "change": 0.45,
            "change_percent": 0.30,
            "timestamp": "2025-11-04T10:30:00",
            "market_cap": 2500000000000,
            "source": "yahoo_finance"
        }
    }
    """
    try:
        source = request.args.get('source')
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        
        manager = get_realtime_manager()
        data = manager.get_realtime_quote(symbol, source=source, use_cache=use_cache)
        
        return jsonify({
            'status': 'success',
            'data': data
        })
    
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@realtime_bp.route('/quotes', methods=['POST'])
def get_multiple_quotes():
    """
    批量获取实时报价
    
    POST /api/v1/realtime/quotes
    
    Request Body:
    {
        "symbols": ["AAPL", "GOOG", "MSFT"],
        "source": "yahoo_finance",  // 可选
        "use_cache": true  // 可选
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "AAPL": {...},
            "GOOG": {...},
            "MSFT": {...}
        },
        "summary": {
            "total": 3,
            "success": 3,
            "failed": 0
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'symbols' not in data:
            return jsonify({
                'status': 'error',
                'message': 'symbols field is required'
            }), 400
        
        symbols = data['symbols']
        source = data.get('source')
        use_cache = data.get('use_cache', True)
        
        if not isinstance(symbols, list) or not symbols:
            return jsonify({
                'status': 'error',
                'message': 'symbols must be a non-empty list'
            }), 400
        
        manager = get_realtime_manager()
        quotes = manager.get_multiple_quotes(symbols, source=source, use_cache=use_cache)
        
        # 统计
        success_count = sum(1 for q in quotes.values() if 'error' not in q)
        failed_count = len(quotes) - success_count
        
        return jsonify({
            'status': 'success',
            'data': quotes,
            'summary': {
                'total': len(quotes),
                'success': success_count,
                'failed': failed_count
            }
        })
    
    except Exception as e:
        logger.error(f"Error fetching multiple quotes: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@realtime_bp.route('/historical/<symbol>', methods=['GET'])
def get_historical(symbol: str):
    """
    获取历史数据
    
    GET /api/v1/realtime/historical/AAPL
    
    Query Parameters:
    - start_date: 开始日期 (YYYY-MM-DD) 必填
    - end_date: 结束日期 (YYYY-MM-DD) 必填
    - source: 数据源 (可选)
    
    Response:
    {
        "status": "success",
        "data": {
            "symbol": "AAPL",
            "records": [
                {
                    "date": "2025-11-01",
                    "open": 150.00,
                    "high": 152.00,
                    "low": 149.50,
                    "close": 151.00,
                    "volume": 75000000
                }
            ],
            "count": 100
        }
    }
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        source = request.args.get('source')
        
        if not start_date or not end_date:
            return jsonify({
                'status': 'error',
                'message': 'start_date and end_date are required'
            }), 400
        
        manager = get_realtime_manager()
        df = manager.get_historical_data(symbol, start_date, end_date, source=source)
        
        # 转换为JSON格式
        records = []
        for idx, row in df.iterrows():
            record = {
                'date': str(idx),
                'open': float(row.get('Open', 0)),
                'high': float(row.get('High', 0)),
                'low': float(row.get('Low', 0)),
                'close': float(row.get('Close', 0)),
                'volume': int(row.get('Volume', 0))
            }
            records.append(record)
        
        return jsonify({
            'status': 'success',
            'data': {
                'symbol': symbol,
                'records': records,
                'count': len(records)
            }
        })
    
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@realtime_bp.route('/market/summary', methods=['GET'])
def get_market_summary():
    """
    获取市场摘要
    
    GET /api/v1/realtime/market/summary
    
    Response:
    {
        "status": "success",
        "data": {
            "total_stocks": 10,
            "valid_quotes": 10,
            "up_count": 6,
            "down_count": 3,
            "unchanged_count": 1,
            "avg_change_percent": 0.5,
            "timestamp": "2025-11-04T10:30:00",
            "quotes": {...}
        }
    }
    """
    try:
        manager = get_realtime_manager()
        summary = manager.get_market_summary()
        
        return jsonify({
            'status': 'success',
            'data': summary
        })
    
    except Exception as e:
        logger.error(f"Error fetching market summary: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@realtime_bp.route('/predict/<symbol>', methods=['GET'])
def predict_realtime(symbol: str):
    """
    实时预测单只股票
    
    GET /api/v1/realtime/predict/AAPL?use_causal=true
    
    Response:
    {
        "status": "success",
        "data": {
            "symbol": "AAPL",
            "timestamp": "2025-11-04T10:30:00",
            "current_price": 150.25,
            "prediction": {
                "direction": "UP",
                "confidence": 0.75,
                "probabilities": {"UP": 0.75, "DOWN": 0.25}
            },
            "market_data": {...}
        }
    }
    """
    try:
        from api.realtime_predictor import get_realtime_predictor
        
        use_causal = request.args.get('use_causal', 'true').lower() == 'true'
        
        predictor = get_realtime_predictor()
        result = predictor.predict_realtime(symbol, use_causal=use_causal)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"Error in realtime prediction for {symbol}: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@realtime_bp.route('/predict/batch', methods=['POST'])
def predict_realtime_batch():
    """
    批量实时预测
    
    POST /api/v1/realtime/predict/batch
    
    Request Body:
    {
        "symbols": ["AAPL", "GOOG", "MSFT"],
        "use_causal": true
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "AAPL": {...},
            "GOOG": {...},
            "MSFT": {...}
        }
    }
    """
    try:
        from api.realtime_predictor import get_realtime_predictor
        
        data = request.get_json()
        
        if not data or 'symbols' not in data:
            return jsonify({
                'status': 'error',
                'message': 'symbols field is required'
            }), 400
        
        symbols = data['symbols']
        use_causal = data.get('use_causal', True)
        
        predictor = get_realtime_predictor()
        results = predictor.predict_realtime_batch(symbols, use_causal=use_causal)
        
        return jsonify({
            'status': 'success',
            'data': results
        })
    
    except Exception as e:
        logger.error(f"Error in batch realtime prediction: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@realtime_bp.route('/predict/horizon/<symbol>', methods=['GET'])
def predict_horizon(symbol: str):
    """
    预测未来多天走势（GET方法）
    
    GET /api/v1/realtime/predict/horizon/AAPL?days=5&use_causal=true
    
    Response:
    {
        "status": "success",
        "data": {
            "symbol": "AAPL",
            "current_price": 150.25,
            "horizon_days": 5,
            "predictions": [
                {
                    "date": "2025-11-05",
                    "predicted_direction": "UP",
                    "confidence": 0.75
                },
                ...
            ]
        }
    }
    """
    try:
        from api.realtime_predictor import get_realtime_predictor
        
        horizon_days = int(request.args.get('days', 5))
        use_causal = request.args.get('use_causal', 'true').lower() == 'true'
        
        if horizon_days < 1 or horizon_days > 30:
            return jsonify({
                'status': 'error',
                'message': 'days must be between 1 and 30'
            }), 400
        
        predictor = get_realtime_predictor()
        result = predictor.predict_with_horizon(symbol, horizon_days, use_causal)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"Error in horizon prediction for {symbol}: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@realtime_bp.route('/predict/horizon', methods=['POST'])
def predict_horizon_post():
    """
    预测未来多天走势（POST方法）
    
    POST /api/v1/realtime/predict/horizon
    
    Request Body:
    {
        "symbol": "AAPL",
        "days": 5,
        "use_causal": true
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "symbol": "AAPL",
            "current_price": 150.25,
            "horizon_days": 5,
            "predictions": [
                {
                    "date": "2025-11-05",
                    "predicted_direction": "UP",
                    "probabilities": {"UP": 0.75, "DOWN": 0.25},
                    "confidence": 0.75
                },
                ...
            ],
            "confidence_analysis": {
                "mean": 0.68,
                "std": 0.12,
                "max": 0.85,
                "min": 0.52
            }
        }
    }
    """
    try:
        from api.realtime_predictor import get_realtime_predictor
        
        data = request.get_json()
        
        if not data or 'symbol' not in data:
            return jsonify({
                'status': 'error',
                'message': 'symbol field is required'
            }), 400
        
        symbol = data['symbol']
        horizon_days = int(data.get('days', 5))
        use_causal = data.get('use_causal', True)
        
        if horizon_days < 1 or horizon_days > 30:
            return jsonify({
                'status': 'error',
                'message': 'days must be between 1 and 30'
            }), 400
        
        predictor = get_realtime_predictor()
        result = predictor.predict_with_horizon(symbol, horizon_days, use_causal)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"Error in horizon prediction for {symbol}: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@realtime_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    清除缓存
    
    POST /api/v1/realtime/cache/clear
    
    Request Body (可选):
    {
        "symbol": "AAPL"  // 清除特定股票缓存，不填则清除所有
    }
    
    Response:
    {
        "status": "success",
        "message": "Cache cleared"
    }
    """
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol')
        
        manager = get_realtime_manager()
        
        if symbol:
            cache_key = f"quote_{symbol}"
            manager.cache.clear(cache_key)
            message = f"Cache cleared for {symbol}"
        else:
            manager.cache.clear()
            message = "All cache cleared"
        
        return jsonify({
            'status': 'success',
            'message': message
        })
    
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== WebSocket 事件处理 ====================

def register_socketio_events(sio):
    """注册SocketIO事件处理器"""
    
    @sio.on('connect', namespace='/realtime')
    def handle_connect():
        """客户端连接"""
        logger.info(f"Client connected: {request.sid}")
        emit('connection_response', {
            'status': 'connected',
            'message': 'Connected to realtime data stream'
        })

    @sio.on('disconnect', namespace='/realtime')
    def handle_disconnect():
        """客户端断开连接"""
        logger.info(f"Client disconnected: {request.sid}")

    @sio.on('subscribe', namespace='/realtime')
    def handle_subscribe(data):
        """
        订阅股票实时数据
        
        客户端发送:
        {
            "symbols": ["AAPL", "GOOG", "MSFT"]
        }
        """
        try:
            symbols = data.get('symbols', [])
            
            if not isinstance(symbols, list):
                emit('error', {'message': 'symbols must be a list'})
                return
            
            # 加入房间（每个股票一个房间）
            for symbol in symbols:
                join_room(f"stock_{symbol}")
                logger.info(f"Client {request.sid} subscribed to {symbol}")
            
            emit('subscribe_response', {
                'status': 'success',
                'subscribed': symbols
            })
            
            # 立即推送当前数据
            manager = get_realtime_manager()
            quotes = manager.get_multiple_quotes(symbols, use_cache=True)
            
            emit('market_update', {
                'type': 'initial',
                'data': quotes
            })
        
        except Exception as e:
            logger.error(f"Error in subscribe: {e}", exc_info=True)
            emit('error', {'message': str(e)})

    @sio.on('unsubscribe', namespace='/realtime')
    def handle_unsubscribe(data):
        """
        取消订阅
        
        客户端发送:
        {
            "symbols": ["AAPL"]
        }
        """
        try:
            symbols = data.get('symbols', [])
            
            for symbol in symbols:
                leave_room(f"stock_{symbol}")
                logger.info(f"Client {request.sid} unsubscribed from {symbol}")
            
            emit('unsubscribe_response', {
                'status': 'success',
                'unsubscribed': symbols
            })
        
        except Exception as e:
            logger.error(f"Error in unsubscribe: {e}", exc_info=True)
            emit('error', {'message': str(e)})


def broadcast_market_update(symbols: List[str], data: Dict):
    """
    广播市场更新（服务器端调用）
    
    Args:
        symbols: 股票代码列表
        data: 更新数据
    """
    if not socketio:
        return
    
    for symbol in symbols:
        socketio.emit(
            'market_update',
            {
                'type': 'update',
                'symbol': symbol,
                'data': data.get(symbol, {})
            },
            room=f"stock_{symbol}",
            namespace='/realtime'
        )


@realtime_bp.route('/model/status', methods=['GET'])
def get_model_status():
    """
    获取模型状态信息
    
    GET /api/v1/realtime/model/status
    
    Response:
    {
        "status": "success",
        "data": {
            "model_loaded": true,
            "model_type": "VAE + GRU",
            "parameters": "2.17M",
            "causal_enabled": true,
            "training_dataset": "CMIN-CN",
            "device": "cuda",
            "inference_speed": "~50ms",
            "checkpoint_path": "checkpoints/xxx/model.pth"
        }
    }
    """
    try:
        from api.realtime_predictor import RealtimePredictor
        import torch
        
        # 获取预测器实例
        predictor = RealtimePredictor()
        
        # 收集模型信息
        model_info = {
            'model_loaded': predictor.predictor.model_loaded,
            'model_type': 'VAE + GRU',
            'parameters': '2.17M',
            'causal_enabled': True,
            'training_dataset': 'CMIN-CN',
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'inference_speed': '~50ms' if predictor.predictor.model_loaded else 'N/A',
            'checkpoint_path': 'checkpoints/best/model.pth' if predictor.predictor.model_loaded else None,
            'prediction_method': 'deep_learning' if predictor.predictor.model_loaded else 'rule_based'
        }
        
        return jsonify({
            'status': 'success',
            'data': model_info
        })
    
    except Exception as e:
        logger.error(f"Error fetching model status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {
                'model_loaded': False,
                'model_type': 'VAE + GRU',
                'parameters': '2.17M',
                'causal_enabled': True,
                'device': 'cpu',
                'prediction_method': 'rule_based'
            }
        }), 500


def register_realtime_routes(app, enable_websocket=False):
    """
    注册实时数据路由
    
    Args:
        app: Flask应用
        enable_websocket: 是否启用WebSocket
    """
    global socketio
    
    app.register_blueprint(realtime_bp)
    
    if enable_websocket:
        socketio = init_socketio(app)
        # 注册WebSocket事件处理器
        register_socketio_events(socketio)
    
    logger.info('Realtime data routes registered successfully')
