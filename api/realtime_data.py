"""
实时数据接入模块
支持多种数据源的实时股票数据获取、缓存和推送
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import time
from abc import ABC, abstractmethod
import json
import os

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """数据源抽象基类"""
    
    @abstractmethod
    def get_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时价格"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取历史数据"""
        pass
    
    @abstractmethod
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取实时报价"""
        pass


class YahooFinanceSource(DataSource):
    """Yahoo Finance数据源"""
    
    def __init__(self):
        try:
            import yfinance as yf
            self.yf = yf
            logger.info("Yahoo Finance data source initialized")
        except ImportError:
            logger.warning("yfinance not installed. Install with: pip install yfinance")
            self.yf = None
    
    def get_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时价格"""
        if not self.yf:
            raise RuntimeError("yfinance not available")
        
        try:
            ticker = self.yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'price': info.get('currentPrice', info.get('regularMarketPrice')),
                'open': info.get('regularMarketOpen'),
                'high': info.get('dayHigh'),
                'low': info.get('dayLow'),
                'volume': info.get('volume'),
                'previous_close': info.get('previousClose'),
                'change': info.get('regularMarketChange'),
                'change_percent': info.get('regularMarketChangePercent'),
                'timestamp': datetime.now().isoformat(),
                'market_cap': info.get('marketCap'),
                'source': 'yahoo_finance'
            }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取历史数据"""
        if not self.yf:
            raise RuntimeError("yfinance not available")
        
        try:
            ticker = self.yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            df['Symbol'] = symbol
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise
    
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取实时报价"""
        if not self.yf:
            raise RuntimeError("yfinance not available")
        
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.get_realtime_price(symbol)
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results


class AlphaVantageSource(DataSource):
    """Alpha Vantage数据源"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            from alpha_vantage.timeseries import TimeSeries
            self.ts = TimeSeries(key=api_key, output_format='pandas')
            logger.info("Alpha Vantage data source initialized")
        except ImportError:
            logger.warning("alpha_vantage not installed. Install with: pip install alpha-vantage")
            self.ts = None
    
    def get_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时价格"""
        if not self.ts:
            raise RuntimeError("alpha_vantage not available")
        
        try:
            data, meta = self.ts.get_quote_endpoint(symbol)
            
            return {
                'symbol': symbol,
                'price': float(data['05. price'].iloc[0]),
                'open': float(data['02. open'].iloc[0]),
                'high': float(data['03. high'].iloc[0]),
                'low': float(data['04. low'].iloc[0]),
                'volume': int(data['06. volume'].iloc[0]),
                'previous_close': float(data['08. previous close'].iloc[0]),
                'change': float(data['09. change'].iloc[0]),
                'change_percent': data['10. change percent'].iloc[0],
                'timestamp': data['07. latest trading day'].iloc[0],
                'source': 'alpha_vantage'
            }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取历史数据"""
        if not self.ts:
            raise RuntimeError("alpha_vantage not available")
        
        try:
            data, meta = self.ts.get_daily(symbol, outputsize='full')
            df = data.loc[start_date:end_date]
            df['Symbol'] = symbol
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise
    
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取实时报价"""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.get_realtime_price(symbol)
                time.sleep(12)  # Alpha Vantage API限制：5 calls/min
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results


class TushareSource(DataSource):
    """Tushare数据源（中国A股）"""
    
    def __init__(self, token: str):
        self.token = token
        try:
            import tushare as ts
            ts.set_token(token)
            self.pro = ts.pro_api()
            logger.info("Tushare data source initialized")
        except ImportError:
            logger.warning("tushare not installed. Install with: pip install tushare")
            self.pro = None
    
    def get_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时价格"""
        if not self.pro:
            raise RuntimeError("tushare not available")
        
        try:
            # Tushare实时数据
            df = self.pro.daily(ts_code=symbol, trade_date=datetime.now().strftime('%Y%m%d'))
            
            if df.empty:
                raise ValueError(f"No data for {symbol}")
            
            row = df.iloc[0]
            return {
                'symbol': symbol,
                'price': row['close'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'volume': row['vol'],
                'previous_close': row['pre_close'],
                'change': row['change'],
                'change_percent': row['pct_chg'],
                'timestamp': datetime.now().isoformat(),
                'source': 'tushare'
            }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取历史数据"""
        if not self.pro:
            raise RuntimeError("tushare not available")
        
        try:
            df = self.pro.daily(
                ts_code=symbol,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
            
            if df.empty:
                logger.warning(f"No historical data returned for {symbol} from {start_date} to {end_date}")
                return pd.DataFrame()
            
            # 标准化列名：Tushare使用小写列名，需要转换
            df = df.rename(columns={
                'trade_date': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'vol': 'Volume'
            })
            
            # 设置日期索引
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
                df.set_index('Date', inplace=True)
                df.sort_index(inplace=True)
            
            df['Symbol'] = symbol
            logger.info(f"Retrieved {len(df)} records for {symbol} from Tushare")
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise
    
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取实时报价"""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.get_realtime_price(symbol)
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir: str = 'cache/realtime', ttl: int = 60):
        """
        初始化数据缓存
        
        Args:
            cache_dir: 缓存目录
            ttl: 缓存过期时间（秒）
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.memory_cache = {}
        self.cache_timestamps = {}
        
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"Data cache initialized with TTL={ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        # 检查内存缓存
        if key in self.memory_cache:
            timestamp = self.cache_timestamps.get(key, 0)
            if time.time() - timestamp < self.ttl:
                return self.memory_cache[key]
            else:
                # 缓存过期，删除
                del self.memory_cache[key]
                del self.cache_timestamps[key]
        
        # 检查文件缓存
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime < self.ttl:
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    # 加载到内存缓存
                    self.memory_cache[key] = data
                    self.cache_timestamps[key] = mtime
                    return data
                except Exception as e:
                    logger.warning(f"Error loading cache file {cache_file}: {e}")
        
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存数据"""
        # 保存到内存
        self.memory_cache[key] = value
        self.cache_timestamps[key] = time.time()
        
        # 保存到文件
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(value, f)
        except Exception as e:
            logger.warning(f"Error saving cache file {cache_file}: {e}")
    
    def clear(self, key: Optional[str] = None):
        """清除缓存"""
        if key:
            # 清除指定键
            self.memory_cache.pop(key, None)
            self.cache_timestamps.pop(key, None)
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
        else:
            # 清除所有缓存
            self.memory_cache.clear()
            self.cache_timestamps.clear()
            for file in os.listdir(self.cache_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, file))


class RealtimeDataManager:
    """实时数据管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化实时数据管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.data_sources = {}
        self.cache = DataCache(
            cache_dir=config.get('cache_dir', 'cache/realtime'),
            ttl=config.get('cache_ttl', 60)
        )
        
        # 初始化数据源
        self._init_data_sources()
        
        # 自动更新线程
        self.auto_update_enabled = config.get('auto_update', False)
        self.update_interval = config.get('update_interval', 300)  # 5分钟
        self.update_thread = None
        
        if self.auto_update_enabled:
            self.start_auto_update()
        
        logger.info("Realtime data manager initialized")
    
    def _init_data_sources(self):
        """初始化数据源"""
        sources_config = self.config.get('data_sources', {})
        
        # Yahoo Finance
        if sources_config.get('yahoo_finance', {}).get('enabled', True):
            try:
                self.data_sources['yahoo_finance'] = YahooFinanceSource()
            except Exception as e:
                logger.warning(f"Failed to initialize Yahoo Finance: {e}")
        
        # Alpha Vantage
        alpha_config = sources_config.get('alpha_vantage', {})
        if alpha_config.get('enabled', False):
            api_key = alpha_config.get('api_key')
            if api_key:
                try:
                    self.data_sources['alpha_vantage'] = AlphaVantageSource(api_key)
                except Exception as e:
                    logger.warning(f"Failed to initialize Alpha Vantage: {e}")
        
        # Tushare
        tushare_config = sources_config.get('tushare', {})
        if tushare_config.get('enabled', False):
            token = tushare_config.get('token')
            if token:
                try:
                    self.data_sources['tushare'] = TushareSource(token)
                except Exception as e:
                    logger.warning(f"Failed to initialize Tushare: {e}")
        
        logger.info(f"Initialized {len(self.data_sources)} data sources: {list(self.data_sources.keys())}")
    
    def get_realtime_quote(self, symbol: str, source: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取实时报价
        
        Args:
            symbol: 股票代码
            source: 指定数据源（可选）
            use_cache: 是否使用缓存
        
        Returns:
            实时报价数据
        """
        cache_key = f"quote_{symbol}"
        
        # 检查缓存
        if use_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {symbol}")
                return cached_data
        
        # 确定数据源
        if source and source in self.data_sources:
            data_source = self.data_sources[source]
        else:
            # 使用第一个可用的数据源
            if not self.data_sources:
                raise RuntimeError("No data sources available")
            data_source = list(self.data_sources.values())[0]
        
        # 获取数据
        try:
            data = data_source.get_realtime_price(symbol)
            
            # 保存到缓存
            if use_cache:
                self.cache.set(cache_key, data)
            
            return data
        except Exception as e:
            logger.error(f"Error fetching realtime quote for {symbol}: {e}")
            raise
    
    def get_multiple_quotes(self, symbols: List[str], source: Optional[str] = None, use_cache: bool = True) -> Dict[str, Dict]:
        """
        批量获取实时报价
        
        Args:
            symbols: 股票代码列表
            source: 指定数据源（可选）
            use_cache: 是否使用缓存
        
        Returns:
            股票代码到报价数据的字典
        """
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.get_realtime_quote(symbol, source, use_cache)
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, 
                           source: Optional[str] = None) -> pd.DataFrame:
        """
        获取历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            source: 指定数据源（可选）
        
        Returns:
            历史数据DataFrame
        """
        if not self.data_sources:
            raise RuntimeError("No data sources available")
        
        # 如果指定了数据源，优先使用
        if source and source in self.data_sources:
            try:
                return self.data_sources[source].get_historical_data(symbol, start_date, end_date)
            except Exception as e:
                logger.warning(f"Specified source {source} failed for {symbol}: {e}")
        
        # 优先级：tushare > yahoo_finance > alpha_vantage
        source_priority = ['tushare', 'yahoo_finance', 'alpha_vantage']
        
        # 按优先级尝试每个可用的数据源
        for source_name in source_priority:
            if source_name in self.data_sources:
                try:
                    logger.info(f"Attempting to fetch historical data for {symbol} from {source_name}")
                    df = self.data_sources[source_name].get_historical_data(symbol, start_date, end_date)
                    if df is not None and not df.empty:
                        logger.info(f"Successfully fetched {len(df)} records for {symbol} from {source_name}")
                        return df
                except Exception as e:
                    logger.warning(f"Failed to fetch from {source_name} for {symbol}: {e}")
                    continue
        
        # 如果所有优先源都失败，尝试剩余的源
        for source_name, data_source in self.data_sources.items():
            if source_name not in source_priority:
                try:
                    logger.info(f"Attempting to fetch historical data for {symbol} from {source_name}")
                    df = data_source.get_historical_data(symbol, start_date, end_date)
                    if df is not None and not df.empty:
                        logger.info(f"Successfully fetched {len(df)} records for {symbol} from {source_name}")
                        return df
                except Exception as e:
                    logger.warning(f"Failed to fetch from {source_name} for {symbol}: {e}")
                    continue
        
        # 所有数据源都失败
        error_msg = f"All data sources failed for {symbol}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def update_cache(self, symbols: List[str]):
        """更新缓存数据"""
        logger.info(f"Updating cache for {len(symbols)} symbols")
        self.get_multiple_quotes(symbols, use_cache=False)
    
    def start_auto_update(self):
        """启动自动更新"""
        if self.update_thread and self.update_thread.is_alive():
            logger.warning("Auto update already running")
            return
        
        def update_loop():
            while self.auto_update_enabled:
                try:
                    # 获取需要更新的股票列表
                    symbols = self.config.get('watch_list', [])
                    if symbols:
                        self.update_cache(symbols)
                except Exception as e:
                    logger.error(f"Error in auto update: {e}")
                
                time.sleep(self.update_interval)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        logger.info(f"Auto update started (interval={self.update_interval}s)")
    
    def stop_auto_update(self):
        """停止自动更新"""
        self.auto_update_enabled = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("Auto update stopped")
    
    def get_market_summary(self) -> Dict[str, Any]:
        """获取市场摘要"""
        watch_list = self.config.get('watch_list', [])
        if not watch_list:
            return {'error': 'No watch list configured'}
        
        quotes = self.get_multiple_quotes(watch_list)
        
        # 计算统计信息
        valid_quotes = [q for q in quotes.values() if 'error' not in q]
        
        if not valid_quotes:
            return {'error': 'No valid quotes available'}
        
        up_count = sum(1 for q in valid_quotes if q.get('change', 0) > 0)
        down_count = sum(1 for q in valid_quotes if q.get('change', 0) < 0)
        
        avg_change = np.mean([q.get('change_percent', 0) for q in valid_quotes])
        
        return {
            'total_stocks': len(watch_list),
            'valid_quotes': len(valid_quotes),
            'up_count': up_count,
            'down_count': down_count,
            'unchanged_count': len(valid_quotes) - up_count - down_count,
            'avg_change_percent': float(avg_change),
            'timestamp': datetime.now().isoformat(),
            'quotes': quotes
        }


# 全局实例
_realtime_manager = None


def get_realtime_manager(config: Optional[Dict] = None) -> RealtimeDataManager:
    """获取实时数据管理器实例（单例）"""
    global _realtime_manager
    
    if _realtime_manager is None:
        if config is None:
            # 默认配置
            config = {
                'cache_dir': 'cache/realtime',
                'cache_ttl': 60,
                'auto_update': False,
                'update_interval': 300,
                'data_sources': {
                    'yahoo_finance': {'enabled': True},
                    'alpha_vantage': {'enabled': False},
                    'tushare': {
                        'enabled': True,
                        'token': os.environ.get('TUSHARE_TOKEN', '')
                    }
                },
                'watch_list': []
            }
        
        _realtime_manager = RealtimeDataManager(config)
    
    return _realtime_manager
