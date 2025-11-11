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
                # 从 DataPipe 获取数据
                # TODO: 实现 DataPipe 接口以获取历史数据
                raw_data = self._get_stock_data(stock_symbol, start_date, end_date)
            else:
                # 生成模拟数据
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
                    # 使用最后一个序列进行预测
                    input_tensor = torch.FloatTensor(sequences[-1:]).to(self.device)
                    
                    # 模型预测
                    with torch.no_grad():
                        output = self.model(input_tensor)
                        probabilities = torch.softmax(output, dim=-1)[0]
                        pred_idx = torch.argmax(probabilities).item()
                        confidence = probabilities[pred_idx].item()
                    
                    direction = 'UP' if pred_idx == 1 else 'DOWN'
                    probs = {
                        'DOWN': probabilities[0].item(),
                        'UP': probabilities[1].item()
                    }
                else:
                    # 序列不足，返回默认预测
                    direction = 'UP'
                    confidence = 0.5
                    probs = {'UP': 0.5, 'DOWN': 0.5}
            else:
                # 无预处理器，使用模拟预测
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
        """从 DataPipe 获取股票数据"""
        # TODO: 实现真实的数据获取逻辑
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
                raise ValueError(f"Stock {stock} not found")
        else:
            stock_idx = 0  # Fallback
        
        # 获取被影响（incoming edges）
        influenced_by_weights = self.graph[:, stock_idx]
        influenced_by_indices = np.argsort(influenced_by_weights)[-top_k:][::-1]
        
        # 获取影响（outgoing edges）
        influences_weights = self.graph[stock_idx, :]
        influences_indices = np.argsort(influences_weights)[-top_k:][::-1]
        
        # 获取股票代码
        if self.stock_mapper:
            influenced_by_stocks = [
                {'stock': self.stock_mapper.get_code(i), 'weight': float(influenced_by_weights[i])}
                for i in influenced_by_indices
                if influenced_by_weights[i] > 0 and self.stock_mapper.get_code(i) is not None
            ]
            influences_stocks = [
                {'stock': self.stock_mapper.get_code(i), 'weight': float(influences_weights[i])}
                for i in influences_indices
                if influences_weights[i] > 0 and self.stock_mapper.get_code(i) is not None
            ]
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
