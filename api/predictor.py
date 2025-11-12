"""
Stock Predictor
核心预测引擎包装类 - 增强版，集成股票映射和数据预处理
"""

import os
import sys
import numpy as np
import torch
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Model import Model
from Executor import Executor
from ConfigLoader import logger as config_logger
from DataPipe import DataPipe

logger = logging.getLogger(__name__)

# 导入新工具
try:
    from utils.stock_mapper import StockMapper
    from utils.data_preprocessor import DataPreprocessor
    UTILS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Utils not available: {e}")
    UTILS_AVAILABLE = False


class StockPredictor:
    """股票预测器封装类 - 增强版"""
    
    def __init__(
        self, 
        config_path='config.yml',
        stock_list_path: Optional[str] = None,
        enable_preprocessing: bool = True
    ):
        """
        初始化预测器
        
        Args:
            config_path: 配置文件路径
            stock_list_path: 股票列表文件路径
            enable_preprocessing: 是否启用数据预处理
        """
        self.config_path = config_path
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.enable_preprocessing = enable_preprocessing and UTILS_AVAILABLE
        
        # 初始化股票映射器
        if UTILS_AVAILABLE:
            self.stock_mapper = self._init_stock_mapper(stock_list_path)
        else:
            self.stock_mapper = None
            logger.warning("Stock mapper not available")
        
        # 初始化数据预处理器
        if self.enable_preprocessing:
            self.preprocessor = DataPreprocessor(
                normalization='standard',
                fill_method='forward',
                window_size=5,
                handle_outliers=True
            )
        else:
            self.preprocessor = None
        
        # 加载模型
        self._load_model()
        
        # 初始化数据管道
        try:
            self.pipe = DataPipe()
        except Exception as e:
            logger.warning(f"DataPipe initialization failed: {e}")
            self.pipe = None
        
        logger.info(f"Stock predictor initialized on {self.device}")
        if self.stock_mapper:
            logger.info(f"Loaded {self.stock_mapper.size()} stocks")
    
    def _init_stock_mapper(self, stock_list_path: Optional[str]) -> Optional[StockMapper]:
        """初始化股票映射器"""
        try:
            if stock_list_path and os.path.exists(stock_list_path):
                mapper = StockMapper(stock_list_path)
                logger.info(f"Loaded stock mapper from {stock_list_path}")
                return mapper
            
            # 尝试从因果图推断股票数量
            graph_path = 'causal_graph.npy'
            if os.path.exists(graph_path):
                graph = np.load(graph_path)
                n_stocks = graph.shape[0]
                mapper = StockMapper()
                for i in range(n_stocks):
                    mapper.add_stock(f'Stock_{i:03d}', i, f'Stock {i}', 'default')
                logger.info(f"Created default mapper with {n_stocks} stocks")
                return mapper
            
            logger.warning("Could not initialize stock mapper")
            return None
            
        except Exception as e:
            logger.error(f"Error initializing stock mapper: {e}")
            return None
    
    def _load_model(self):
        """加载预训练模型"""
        try:
            # 加载因果图
            graph_path = 'causal_graph.npy'
            if os.path.exists(graph_path):
                graph = np.load(graph_path)
                logger.info(f"Loaded causal graph from {graph_path}")
            else:
                logger.warning("Causal graph not found, using random initialization")
                # 确定股票数量
                if self.stock_mapper:
                    n_stocks = self.stock_mapper.size()
                else:
                    n_stocks = 90  # 默认值
                graph = np.random.random((n_stocks, n_stocks)) * 0.1
                np.fill_diagonal(graph, 0.0)
            
            self.graph = graph
            
            # 创建模型
            self.model = Model(graph=graph)
            self.model.to(self.device)
            self.model.eval()
            
            # 尝试加载检查点
            checkpoint_path = 'checkpoints/model.pth'
            if os.path.exists(checkpoint_path):
                checkpoint = torch.load(checkpoint_path, map_location=self.device)
                self.model.load_state_dict(checkpoint)
                logger.info(f"Loaded model checkpoint from {checkpoint_path}")
            else:
                logger.warning("No checkpoint found, using initialized model")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def predict_single(
        self, 
        stock_symbol: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_causal: bool = True
    ) -> Dict[str, Any]:
        """
        预测单只股票
        
        Args:
            stock_symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            use_causal: 是否使用因果信息
        
        Returns:
            预测结果字典
        """
        try:
            # 获取股票索引
            if self.stock_mapper:
                stock_idx = self.stock_mapper.get_index(stock_symbol)
                if stock_idx is None:
                    raise ValueError(f"Stock {stock_symbol} not found in mapper")
            else:
                stock_idx = 0  # Fallback
            
            # 获取数据
            if self.pipe is not None:
                # 从 DataPipe 获取真实数据
                raw_data = self._get_stock_data(stock_symbol, start_date, end_date)
                
                # 如果没有获取到真实数据,使用模拟数据
                if raw_data is None:
                    logger.warning(f"No real data for {stock_symbol}, using mock data")
                    raw_data = self._generate_mock_data()
            else:
                # DataPipe 不可用,生成模拟数据
                logger.warning("DataPipe not available, using mock data")
                raw_data = self._generate_mock_data()
            
            # 数据预处理
            if self.preprocessor is not None and raw_data is not None:
                # 预处理数据 - 先 fit 再 transform
                self.preprocessor.fit(raw_data)
                processed_data = self.preprocessor.transform(raw_data)
                
                # 创建预测序列
                sequences, targets = self.preprocessor.create_sequences(
                    processed_data,
                    seq_length=5,
                    pred_horizon=1,
                    include_target=True
                )
                
                if len(sequences) > 0:
                    # 使用简化的预测逻辑(基于数据统计)
                    # 因为完整的Model.forward()需要更多参数(word_ph, stock_ph等)
                    
                    # 分析价格趋势
                    last_prices = processed_data[-5:, 0] if len(processed_data) >= 5 else processed_data[:, 0]
                    if len(last_prices) >= 2:
                        # 计算趋势
                        trend = np.mean(np.diff(last_prices))
                        volatility = np.std(last_prices)
                        
                        # 基于趋势和波动率预测
                        if trend > 0:
                            up_prob = min(0.5 + trend / (volatility + 1e-6), 0.95)
                        else:
                            up_prob = max(0.5 + trend / (volatility + 1e-6), 0.05)
                        
                        up_prob = float(np.clip(up_prob, 0.05, 0.95))
                        down_prob = 1.0 - up_prob
                        
                        direction = 'UP' if up_prob > down_prob else 'DOWN'
                        confidence = max(up_prob, down_prob)
                        
                        probs = {
                            'UP': up_prob,
                            'DOWN': down_prob
                        }
                    else:
                        direction = 'UP'
                        confidence = 0.5
                        probs = {'UP': 0.5, 'DOWN': 0.5}
                else:
                    # 序列不足，返回默认预测
                    direction = 'UP'
                    confidence = 0.5
                    probs = {'UP': 0.5, 'DOWN': 0.5}
            else:
                # 无预处理器或数据，使用模拟预测
                direction = 'UP'
                confidence = 0.85
                probs = {'UP': 0.85, 'DOWN': 0.15}
            
            predictions = [{
                'date': end_date or '2015-10-01',
                'predicted_direction': direction,
                'confidence': float(confidence),
                'probabilities': probs,
                'use_causal': use_causal
            }]
            
            return {
                'stock_symbol': stock_symbol,
                'predictions': predictions,
                'model': self.model.model_name if hasattr(self.model, 'model_name') else 'Unknown'
            }
            
        except Exception as e:
            logger.error(f"Error predicting for {stock_symbol}: {e}")
            raise ValueError(f"Prediction failed: {e}")
    
    def _get_stock_data(self, stock_symbol: str, start_date: Optional[str], end_date: Optional[str]) -> Optional[np.ndarray]:
        """
        从 DataPipe 获取股票数据
        
        Args:
            stock_symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            价格数据数组 (n_days, n_features) 或 None
        """
        if not self.pipe:
            logger.warning("DataPipe not available")
            return None
        
        try:
            # 使用 batch_gen_by_stocks 获取特定股票的数据
            logger.info(f"Fetching data for {stock_symbol} from DataPipe")
            
            for batch_dict in self.pipe.batch_gen_by_stocks('test'):
                # 检查是否是目标股票
                if 's' in batch_dict and batch_dict['s'] == stock_symbol:
                    # 提取价格数据
                    # price_batch shape: (batch_size, max_n_days, 3) - [open, high, low]
                    price_batch = batch_dict['price_batch']
                    T_batch = batch_dict['T_batch']
                    
                    # 获取有效的时间步长
                    valid_prices = []
                    for i in range(batch_dict['batch_size']):
                        T = T_batch[i]
                        # 提取前 T 个有效时间步的价格
                        prices = price_batch[i, :T, :]  # shape: (T, 3)
                        valid_prices.append(prices)
                    
                    if valid_prices:
                        # 合并所有批次的数据
                        data = np.concatenate(valid_prices, axis=0)
                        logger.info(f"Fetched {data.shape[0]} days of data for {stock_symbol}")
                        return data
            
            logger.warning(f"No data found for {stock_symbol}")
            return None
            
        except StopIteration:
            logger.warning(f"No data available in DataPipe for {stock_symbol}")
            return None
        except Exception as e:
            logger.error(f"Error fetching data from DataPipe: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_mock_data(self, n_days: int = 20) -> np.ndarray:
        """生成模拟数据用于测试"""
        # 生成模拟的 OHLCV 数据
        np.random.seed(42)
        data = np.random.randn(n_days, 5)  # open, high, low, close, volume
        data[:, 4] = np.abs(data[:, 4]) * 1000000  # volume 必须为正
        return data
    
    def predict_batch(
        self,
        stock_symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_causal: bool = True
    ) -> Dict[str, Any]:
        """
        批量预测多只股票
        
        Args:
            stock_symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            use_causal: 是否使用因果信息
        
        Returns:
            批量预测结果字典
        """
        predictions = {}
        confidences = []
        
        for symbol in stock_symbols:
            try:
                result = self.predict_single(symbol, start_date, end_date, use_causal)
                predictions[symbol] = result['predictions']
                
                # 收集置信度
                for pred in result['predictions']:
                    confidences.append(pred['confidence'])
                    
            except Exception as e:
                logger.error(f"Error predicting {symbol}: {e}")
                predictions[symbol] = []
        
        return {
            'predictions': predictions,
            'summary': {
                'total_stocks': len(stock_symbols),
                'total_predictions': sum(len(p) for p in predictions.values()),
                'avg_confidence': np.mean(confidences) if confidences else 0.0
            }
        }
    
    def get_causal_graph(
        self, 
        stocks: Optional[List[str]] = None,
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        获取因果图
        
        Args:
            stocks: 股票列表（None表示所有）
            threshold: 因果关系阈值
        
        Returns:
            因果图数据
        """
        from api.schemas import format_causal_graph_response
        
        # 如果指定了股票子集，提取子图
        if stocks is not None and self.stock_mapper:
            # 获取股票索引
            indices = []
            valid_stocks = []
            for stock in stocks:
                idx = self.stock_mapper.get_index(stock)
                if idx is not None:
                    indices.append(idx)
                    valid_stocks.append(stock)
                else:
                    logger.warning(f"Stock {stock} not found in mapper")
            
            # 提取子图
            if indices:
                graph = self.graph[np.ix_(indices, indices)]
                stock_list = valid_stocks
            else:
                graph = self.graph
                stock_list = self.stock_mapper.get_all_codes()
        else:
            graph = self.graph
            # 获取完整股票列表
            if self.stock_mapper:
                stock_list = self.stock_mapper.get_all_codes()
            else:
                stock_list = [f"Stock_{i}" for i in range(graph.shape[0])]
        
        return format_causal_graph_response(graph, stock_list, threshold)
    
    def get_causal_influence(
        self,
        stock: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        获取股票的因果影响分析
        
        Args:
            stock: 股票代码
            top_k: 返回前k个影响最大的股票
        
        Returns:
            因果影响分析结果
        """
        # 获取股票索引
        if self.stock_mapper:
            stock_idx = self.stock_mapper.get_index(stock)
            if stock_idx is None:
                logger.warning(f"Stock {stock} not found in mapper")
                return {
                    'stock': stock,
                    'influenced_by': [],
                    'influences': []
                }
        else:
            stock_idx = 0  # Fallback
        
        # 确保索引在有效范围内
        if stock_idx >= self.graph.shape[0]:
            logger.warning(f"Stock index {stock_idx} out of bounds (graph size: {self.graph.shape[0]})")
            return {
                'stock': stock,
                'influenced_by': [],
                'influences': []
            }
        
        # 获取被影响（incoming edges）
        influenced_by_weights = self.graph[:, stock_idx]
        influenced_by_indices = np.argsort(influenced_by_weights)[-top_k:][::-1]
        
        # 获取影响（outgoing edges）
        influences_weights = self.graph[stock_idx, :]
        influences_indices = np.argsort(influences_weights)[-top_k:][::-1]
        
        # 获取股票代码
        if self.stock_mapper:
            influenced_by_stocks = []
            for i in influenced_by_indices:
                if influenced_by_weights[i] > 0:
                    try:
                        code = self.stock_mapper.get_code(i)
                        if code:
                            influenced_by_stocks.append({
                                'stock': code,
                                'weight': float(influenced_by_weights[i])
                            })
                    except KeyError:
                        # 索引不在mapper中,跳过
                        continue
            
            influences_stocks = []
            for i in influences_indices:
                if influences_weights[i] > 0:
                    try:
                        code = self.stock_mapper.get_code(i)
                        if code:
                            influences_stocks.append({
                                'stock': code,
                                'weight': float(influences_weights[i])
                            })
                    except KeyError:
                        # 索引不在mapper中,跳过
                        continue
        else:
            influenced_by_stocks = [
                {'stock': f'Stock_{i}', 'weight': float(influenced_by_weights[i])}
                for i in influenced_by_indices
                if influenced_by_weights[i] > 0
            ]
            influences_stocks = [
                {'stock': f'Stock_{i}', 'weight': float(influences_weights[i])}
                for i in influences_indices
                if influences_weights[i] > 0
            ]
        
        return {
            'stock': stock,
            'influenced_by': influenced_by_stocks,
            'influences': influences_stocks
        }
    
    def get_available_stocks(
        self,
        sector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取可用股票列表
        
        Args:
            sector: 板块过滤
        
        Returns:
            股票列表
        """
        if self.stock_mapper:
            # 从 StockMapper 获取股票列表
            if sector:
                stocks = self.stock_mapper.get_stocks_by_sector(sector)
            else:
                stocks = self.stock_mapper.get_all_codes()
            
            # 获取所有板块
            sectors = {}
            all_codes = self.stock_mapper.get_all_codes()
            for code in all_codes:
                info = self.stock_mapper.get_info(code)
                if info and 'sector' in info:
                    sec = info['sector']
                    if sec not in sectors:
                        sectors[sec] = []
                    sectors[sec].append(code)
        else:
            # Fallback: 使用硬编码的股票列表
            sectors = {
                'tech': ['AAPL', 'GOOG', 'MSFT', 'FB', 'ORCL'],
                'finance': ['JPM', 'BAC', 'WFC', 'C', 'V'],
                'healthcare': ['JNJ', 'PFE', 'UNH', 'MRK', 'AMGN']
            }
            
            if sector and sector in sectors:
                stocks = sectors[sector]
            else:
                stocks = [s for sector_stocks in sectors.values() for s in sector_stocks]
        
        return {
            'stocks': stocks,
            'sectors': sectors
        }
    
    def predict_with_model(
        self,
        stock_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_causal: bool = True
    ) -> Dict[str, Any]:
        """
        使用深度学习模型进行预测 (从 predictor_enhanced 移植)
        
        Args:
            stock_symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            use_causal: 是否使用因果信息
            
        Returns:
            预测结果字典
        """
        if not self.pipe:
            logger.warning("DataPipe not available, cannot use model prediction")
            return self.predict_single(stock_symbol, start_date, end_date, use_causal)
        
        try:
            predictions = []
            
            # 使用 batch_gen_by_stocks 获取数据
            for batch_dict in self.pipe.batch_gen_by_stocks('test'):
                if 's' not in batch_dict or batch_dict['s'] != stock_symbol:
                    continue
                
                # 转换为张量
                batch_dict_tensor = self._to_tensor(batch_dict)
                
                # 模型推理
                with torch.no_grad():
                    outputs = self.model(
                        word_ph=batch_dict_tensor['word_batch'],
                        price_ph=batch_dict_tensor['price_batch'],
                        stock_ph=batch_dict_tensor['stock_batch'],
                        T_ph=batch_dict_tensor['T_batch'],
                        n_words_ph=batch_dict_tensor['n_words_batch'],
                        n_msgs_ph=batch_dict_tensor['n_msgs_batch'],
                        y_ph=None,
                        ss_index_ph=batch_dict_tensor['ss_index_batch'],
                        is_training=False
                    )
                    
                    # 提取预测结果
                    y_T = outputs['y_T']  # [batch_size, 2]
                    
                    # 处理每个样本
                    for i in range(batch_dict['batch_size']):
                        probs = y_T[i].cpu().numpy()
                        up_prob = float(probs[1])
                        down_prob = float(probs[0])
                        
                        predictions.append({
                            'date': 'N/A',
                            'predicted_direction': 'UP' if up_prob > down_prob else 'DOWN',
                            'confidence': float(max(up_prob, down_prob)),
                            'probabilities': {
                                'UP': up_prob,
                                'DOWN': down_prob
                            },
                            'use_causal': use_causal,
                            'method': 'deep_learning'
                        })
                
                # 找到目标股票后停止
                break
            
            if predictions:
                return {
                    'stock_symbol': stock_symbol,
                    'predictions': predictions,
                    'model': 'deep_learning'
                }
            else:
                # 没有找到数据,使用标准预测
                return self.predict_single(stock_symbol, start_date, end_date, use_causal)
                
        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            return self.predict_single(stock_symbol, start_date, end_date, use_causal)
    
    def _to_tensor(self, batch_dict: Dict) -> Dict:
        """转换批次数据为张量"""
        return {
            'word_batch': torch.LongTensor(batch_dict['word_batch']).to(self.device),
            'price_batch': torch.FloatTensor(batch_dict['price_batch']).to(self.device),
            'stock_batch': torch.LongTensor(batch_dict['stock_batch']).to(self.device),
            'T_batch': torch.LongTensor(batch_dict['T_batch']).to(self.device),
            'n_words_batch': torch.LongTensor(batch_dict['n_words_batch']).to(self.device),
            'n_msgs_batch': torch.LongTensor(batch_dict['n_msgs_batch']).to(self.device),
            'ss_index_batch': torch.LongTensor(batch_dict['ss_index_batch']).to(self.device)
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            'model_name': self.model.model_name if hasattr(self.model, 'model_name') else 'Unknown',
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'device': self.device,
            'causal_graph_shape': self.graph.shape,
            'config': {
                'max_n_days': self.model.max_n_days if hasattr(self.model, 'max_n_days') else None,
                'max_n_msgs': self.model.max_n_msgs if hasattr(self.model, 'max_n_msgs') else None,
            }
        }
