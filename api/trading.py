"""
模拟交易系统 API
提供虚拟股票交易功能
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TradingSimulator:
    """模拟交易系统"""
    
    def __init__(self, data_dir: str = "data/trading"):
        """
        初始化交易系统
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.users_file = self.data_dir / "users.json"
        self.transactions_file = self.data_dir / "transactions.json"
        self.leaderboard_file = self.data_dir / "leaderboard.json"
        
        # 初始化数据文件
        self._init_data_files()
        
        # 模拟股价数据（实际应该从真实API获取）
        self.stock_prices = self._init_stock_prices()
        
    def _init_data_files(self):
        """初始化数据文件"""
        if not self.users_file.exists():
            self._save_json(self.users_file, {})
        if not self.transactions_file.exists():
            self._save_json(self.transactions_file, [])
        if not self.leaderboard_file.exists():
            self._save_json(self.leaderboard_file, [])
    
    def _save_json(self, file_path: Path, data: Any):
        """保存JSON数据"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_json(self, file_path: Path) -> Any:
        """加载JSON数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _init_stock_prices(self) -> Dict[str, float]:
        """初始化模拟股价"""
        # 主流科技股模拟价格（美元）
        return {
            'AAPL': 178.50,
            'MSFT': 378.25,
            'GOOG': 141.80,
            'AMZN': 178.35,
            'TSLA': 242.84,
            'FB': 484.03,
            'NVDA': 875.28,
            'JPM': 194.85,
            'JNJ': 158.47,
            'BAC': 36.92,
            'WFC': 57.82,
            'INTC': 23.45,
            'CSCO': 57.31,
            'PFE': 26.14,
            'KO': 62.85,
            'PEP': 166.50,
            'MRK': 109.82,
            'ORCL': 175.23,
            'CVX': 159.47,
            'XOM': 119.58,
            'BP': 35.62,
            'TOT': 68.45,
            'PTR': 97.23,
            'C': 65.84,
            'HSBC': 44.52,
            'MA': 487.93,
            'ABBV': 183.42,
            'AMGN': 277.58,
            'BHP': 56.83,
            'MDT': 87.45,
            'MO': 52.76,
            'NVS': 108.94,
            'PG': 166.28,
            'PM': 119.73,
            'RY': 117.42,
            'TD': 65.89,
            'UL': 59.87,
        }
    
    def create_user(self, user_id: str, username: str, initial_cash: float = 100000.0) -> Dict[str, Any]:
        """
        创建新用户账户
        
        Args:
            user_id: 用户ID
            username: 用户名
            initial_cash: 初始资金（默认10万美元）
            
        Returns:
            用户信息
        """
        users = self._load_json(self.users_file)
        
        if user_id in users:
            raise ValueError(f"User {user_id} already exists")
        
        user_data = {
            'user_id': user_id,
            'username': username,
            'cash': initial_cash,
            'initial_cash': initial_cash,
            'portfolio': {},  # {stock_symbol: {shares: int, avg_price: float}}
            'total_trades': 0,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        users[user_id] = user_data
        self._save_json(self.users_file, users)
        
        logger.info(f"Created user {username} ({user_id}) with ${initial_cash:,.2f}")
        return user_data
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """获取用户信息"""
        users = self._load_json(self.users_file)
        
        if user_id not in users:
            raise ValueError(f"User {user_id} not found")
        
        return users[user_id]
    
    def get_stock_price(self, symbol: str) -> float:
        """
        获取股票当前价格
        
        Args:
            symbol: 股票代码
            
        Returns:
            当前价格
        """
        if symbol not in self.stock_prices:
            raise ValueError(f"Stock {symbol} not found")
        
        # 添加±2%的随机波动
        import random
        base_price = self.stock_prices[symbol]
        fluctuation = random.uniform(-0.02, 0.02)
        return round(base_price * (1 + fluctuation), 2)
    
    def buy_stock(
        self, 
        user_id: str, 
        symbol: str, 
        shares: int
    ) -> Dict[str, Any]:
        """
        买入股票
        
        Args:
            user_id: 用户ID
            symbol: 股票代码
            shares: 股数
            
        Returns:
            交易结果
        """
        if shares <= 0:
            raise ValueError("Shares must be positive")
        
        users = self._load_json(self.users_file)
        user = users.get(user_id)
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # 获取当前价格
        price = self.get_stock_price(symbol)
        total_cost = price * shares
        commission = total_cost * 0.001  # 0.1% 手续费
        total_with_fee = total_cost + commission
        
        # 检查余额
        if user['cash'] < total_with_fee:
            raise ValueError(
                f"Insufficient funds: need ${total_with_fee:,.2f}, have ${user['cash']:,.2f}"
            )
        
        # 更新持仓
        portfolio = user.get('portfolio', {})
        if symbol in portfolio:
            # 更新平均成本
            old_shares = portfolio[symbol]['shares']
            old_avg_price = portfolio[symbol]['avg_price']
            new_shares = old_shares + shares
            new_avg_price = (old_shares * old_avg_price + shares * price) / new_shares
            
            portfolio[symbol]['shares'] = new_shares
            portfolio[symbol]['avg_price'] = round(new_avg_price, 2)
        else:
            portfolio[symbol] = {
                'shares': shares,
                'avg_price': price
            }
        
        # 更新现金和持仓
        user['cash'] = round(user['cash'] - total_with_fee, 2)
        user['portfolio'] = portfolio
        user['total_trades'] += 1
        user['last_updated'] = datetime.now().isoformat()
        
        users[user_id] = user
        self._save_json(self.users_file, users)
        
        # 记录交易
        transaction = {
            'transaction_id': f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id[:8]}",
            'user_id': user_id,
            'type': 'BUY',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'total_cost': total_cost,
            'commission': commission,
            'timestamp': datetime.now().isoformat()
        }
        
        transactions = self._load_json(self.transactions_file)
        transactions.append(transaction)
        self._save_json(self.transactions_file, transactions)
        
        logger.info(f"User {user_id} bought {shares} shares of {symbol} at ${price}")
        
        return {
            'success': True,
            'transaction': transaction,
            'remaining_cash': user['cash'],
            'portfolio': portfolio[symbol]
        }
    
    def sell_stock(
        self, 
        user_id: str, 
        symbol: str, 
        shares: int
    ) -> Dict[str, Any]:
        """
        卖出股票
        
        Args:
            user_id: 用户ID
            symbol: 股票代码
            shares: 股数
            
        Returns:
            交易结果
        """
        if shares <= 0:
            raise ValueError("Shares must be positive")
        
        users = self._load_json(self.users_file)
        user = users.get(user_id)
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # 检查持仓
        portfolio = user.get('portfolio', {})
        if symbol not in portfolio:
            raise ValueError(f"No position in {symbol}")
        
        if portfolio[symbol]['shares'] < shares:
            raise ValueError(
                f"Insufficient shares: trying to sell {shares}, have {portfolio[symbol]['shares']}"
            )
        
        # 获取当前价格
        price = self.get_stock_price(symbol)
        total_revenue = price * shares
        commission = total_revenue * 0.001  # 0.1% 手续费
        net_revenue = total_revenue - commission
        
        # 计算盈亏
        avg_cost = portfolio[symbol]['avg_price']
        profit = (price - avg_cost) * shares
        profit_percent = ((price - avg_cost) / avg_cost) * 100
        
        # 更新持仓
        portfolio[symbol]['shares'] -= shares
        if portfolio[symbol]['shares'] == 0:
            del portfolio[symbol]
        
        # 更新现金
        user['cash'] = round(user['cash'] + net_revenue, 2)
        user['portfolio'] = portfolio
        user['total_trades'] += 1
        user['last_updated'] = datetime.now().isoformat()
        
        users[user_id] = user
        self._save_json(self.users_file, users)
        
        # 记录交易
        transaction = {
            'transaction_id': f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id[:8]}",
            'user_id': user_id,
            'type': 'SELL',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'total_revenue': total_revenue,
            'commission': commission,
            'net_revenue': net_revenue,
            'profit': round(profit, 2),
            'profit_percent': round(profit_percent, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        transactions = self._load_json(self.transactions_file)
        transactions.append(transaction)
        self._save_json(self.transactions_file, transactions)
        
        logger.info(
            f"User {user_id} sold {shares} shares of {symbol} at ${price}, "
            f"profit: ${profit:,.2f} ({profit_percent:.2f}%)"
        )
        
        return {
            'success': True,
            'transaction': transaction,
            'remaining_cash': user['cash'],
            'profit': round(profit, 2),
            'profit_percent': round(profit_percent, 2)
        }
    
    def get_portfolio_value(self, user_id: str) -> Dict[str, Any]:
        """
        获取投资组合总价值
        
        Args:
            user_id: 用户ID
            
        Returns:
            组合价值信息
        """
        user = self.get_user(user_id)
        portfolio = user.get('portfolio', {})
        
        holdings = []
        total_market_value = 0.0
        total_cost = 0.0
        
        for symbol, position in portfolio.items():
            shares = position['shares']
            avg_price = position['avg_price']
            current_price = self.get_stock_price(symbol)
            
            market_value = current_price * shares
            cost = avg_price * shares
            profit = market_value - cost
            profit_percent = (profit / cost) * 100 if cost > 0 else 0
            
            holdings.append({
                'symbol': symbol,
                'shares': shares,
                'avg_price': avg_price,
                'current_price': current_price,
                'market_value': round(market_value, 2),
                'cost': round(cost, 2),
                'profit': round(profit, 2),
                'profit_percent': round(profit_percent, 2)
            })
            
            total_market_value += market_value
            total_cost += cost
        
        total_assets = user['cash'] + total_market_value
        total_profit = total_assets - user['initial_cash']
        total_return = (total_profit / user['initial_cash']) * 100 if user['initial_cash'] > 0 else 0
        
        return {
            'user_id': user_id,
            'username': user['username'],
            'cash': user['cash'],
            'holdings': holdings,
            'total_market_value': round(total_market_value, 2),
            'total_cost': round(total_cost, 2),
            'total_assets': round(total_assets, 2),
            'total_profit': round(total_profit, 2),
            'total_return': round(total_return, 2),
            'initial_cash': user['initial_cash']
        }
    
    def get_transaction_history(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取交易历史
        
        Args:
            user_id: 用户ID
            limit: 返回记录数
            
        Returns:
            交易记录列表
        """
        transactions = self._load_json(self.transactions_file)
        
        # 过滤用户的交易
        user_transactions = [
            tx for tx in transactions 
            if tx['user_id'] == user_id
        ]
        
        # 按时间倒序排序
        user_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return user_transactions[:limit]
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取收益排行榜
        
        Args:
            limit: 返回名次数
            
        Returns:
            排行榜列表
        """
        users = self._load_json(self.users_file)
        
        leaderboard = []
        for user_id, user in users.items():
            portfolio_value = self.get_portfolio_value(user_id)
            
            leaderboard.append({
                'user_id': user_id,
                'username': user['username'],
                'total_assets': portfolio_value['total_assets'],
                'total_return': portfolio_value['total_return'],
                'total_trades': user['total_trades']
            })
        
        # 按总收益率排序
        leaderboard.sort(key=lambda x: x['total_return'], reverse=True)
        
        # 添加排名
        for idx, entry in enumerate(leaderboard[:limit], 1):
            entry['rank'] = idx
        
        return leaderboard[:limit]
    
    def reset_user(self, user_id: str) -> Dict[str, Any]:
        """
        重置用户账户
        
        Args:
            user_id: 用户ID
            
        Returns:
            重置后的用户信息
        """
        users = self._load_json(self.users_file)
        
        if user_id not in users:
            raise ValueError(f"User {user_id} not found")
        
        user = users[user_id]
        user['cash'] = user['initial_cash']
        user['portfolio'] = {}
        user['total_trades'] = 0
        user['last_updated'] = datetime.now().isoformat()
        
        users[user_id] = user
        self._save_json(self.users_file, users)
        
        logger.info(f"Reset user {user_id}")
        return user
