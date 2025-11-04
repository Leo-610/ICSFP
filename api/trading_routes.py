"""
模拟交易系统 API 路由
"""

from flask import Blueprint, jsonify, request
import logging

from api.trading import TradingSimulator

logger = logging.getLogger(__name__)

# 创建蓝图
trading_bp = Blueprint('trading', __name__, url_prefix='/api/v1/trading')

# 全局交易系统实例
_trading_system = None


def get_trading_system():
    """获取交易系统实例（单例模式）"""
    global _trading_system
    if _trading_system is None:
        _trading_system = TradingSimulator()
    return _trading_system


@trading_bp.route('/user/create', methods=['POST'])
def create_user():
    """
    创建新用户账户
    
    Request Body:
    {
        "user_id": "user123",
        "username": "张三",
        "initial_cash": 100000
    }
    """
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        username = data.get('username')
        initial_cash = data.get('initial_cash', 100000.0)
        
        if not user_id or not username:
            return jsonify({
                'status': 'error',
                'message': 'user_id and username are required'
            }), 400
        
        trading = get_trading_system()
        user = trading.create_user(user_id, username, initial_cash)
        
        return jsonify({
            'status': 'success',
            'data': user
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Create user error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trading_bp.route('/user/<user_id>', methods=['GET'])
def get_user(user_id: str):
    """
    获取用户信息
    """
    try:
        trading = get_trading_system()
        user = trading.get_user(user_id)
        
        return jsonify({
            'status': 'success',
            'data': user
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404
    except Exception as e:
        logger.error(f"Get user error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trading_bp.route('/portfolio/<user_id>', methods=['GET'])
def get_portfolio(user_id: str):
    """
    获取用户投资组合
    """
    try:
        trading = get_trading_system()
        portfolio = trading.get_portfolio_value(user_id)
        
        return jsonify({
            'status': 'success',
            'data': portfolio
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404
    except Exception as e:
        logger.error(f"Get portfolio error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trading_bp.route('/trade/buy', methods=['POST'])
def buy_stock():
    """
    买入股票
    
    Request Body:
    {
        "user_id": "user123",
        "symbol": "AAPL",
        "shares": 10
    }
    """
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        symbol = data.get('symbol')
        shares = data.get('shares')
        
        if not all([user_id, symbol, shares]):
            return jsonify({
                'status': 'error',
                'message': 'user_id, symbol, and shares are required'
            }), 400
        
        trading = get_trading_system()
        result = trading.buy_stock(user_id, symbol, int(shares))
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Buy stock error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trading_bp.route('/trade/sell', methods=['POST'])
def sell_stock():
    """
    卖出股票
    
    Request Body:
    {
        "user_id": "user123",
        "symbol": "AAPL",
        "shares": 5
    }
    """
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        symbol = data.get('symbol')
        shares = data.get('shares')
        
        if not all([user_id, symbol, shares]):
            return jsonify({
                'status': 'error',
                'message': 'user_id, symbol, and shares are required'
            }), 400
        
        trading = get_trading_system()
        result = trading.sell_stock(user_id, symbol, int(shares))
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Sell stock error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trading_bp.route('/history/<user_id>', methods=['GET'])
def get_transaction_history(user_id: str):
    """
    获取交易历史
    
    Query Parameters:
    - limit: 返回记录数（默认50）
    """
    try:
        limit = int(request.args.get('limit', 50))
        
        trading = get_trading_system()
        history = trading.get_transaction_history(user_id, limit)
        
        return jsonify({
            'status': 'success',
            'data': {
                'transactions': history,
                'total': len(history)
            }
        })
        
    except Exception as e:
        logger.error(f"Get history error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trading_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """
    获取收益排行榜
    
    Query Parameters:
    - limit: 返回名次（默认10）
    """
    try:
        limit = int(request.args.get('limit', 10))
        
        trading = get_trading_system()
        leaderboard = trading.get_leaderboard(limit)
        
        return jsonify({
            'status': 'success',
            'data': {
                'leaderboard': leaderboard,
                'total': len(leaderboard)
            }
        })
        
    except Exception as e:
        logger.error(f"Get leaderboard error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trading_bp.route('/price/<symbol>', methods=['GET'])
def get_stock_price(symbol: str):
    """
    获取股票当前价格
    """
    try:
        trading = get_trading_system()
        price = trading.get_stock_price(symbol)
        
        return jsonify({
            'status': 'success',
            'data': {
                'symbol': symbol,
                'price': price
            }
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404
    except Exception as e:
        logger.error(f"Get price error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trading_bp.route('/user/<user_id>/reset', methods=['POST'])
def reset_user(user_id: str):
    """
    重置用户账户
    """
    try:
        trading = get_trading_system()
        user = trading.reset_user(user_id)
        
        return jsonify({
            'status': 'success',
            'data': user,
            'message': 'Account reset successfully'
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404
    except Exception as e:
        logger.error(f"Reset user error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


def register_trading_routes(app):
    """注册交易路由到应用"""
    app.register_blueprint(trading_bp)
    logger.info('Trading routes registered successfully')
