"""
Stock Predictor
核心预测引擎包装类
"""

import os
import sys
import numpy as np
import torch
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Model import Model
from Executor import Executor
from ConfigLoader import logger as config_logger
from DataPipe import DataPipe

logger = logging.getLogger(__name__)


class StockPredictor:
    """股票预测器封装类"""
    
    def __init__(self, config_path='config.yml'):
        """
        初始化预测器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # 加载模型
        self._load_model()
        
        # 初始化数据管道
        self.pipe = DataPipe()
        
        logger.info(f"Stock predictor initialized on {self.device}")
    
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
                # 生成默认图（这里需要根据实际股票数量调整）
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
            # 准备数据
            # 这里需要根据实际的DataPipe接口调整
            predictions = []
            
            # 示例预测结果（实际应调用模型）
            # TODO: 实现真实的预测逻辑
            predictions.append({
                'date': start_date or '2015-10-01',
                'predicted_direction': 'UP',
                'confidence': 0.85,
                'probabilities': {'UP': 0.85, 'DOWN': 0.15},
                'use_causal': use_causal
            })
            
            return {
                'stock_symbol': stock_symbol,
                'predictions': predictions,
                'model': self.model.model_name if hasattr(self.model, 'model_name') else 'Unknown'
            }
            
        except Exception as e:
            logger.error(f"Error predicting for {stock_symbol}: {e}")
            raise ValueError(f"Prediction failed: {e}")
    
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
        if stocks is not None:
            # TODO: 根据股票代码获取索引并提取子图
            graph = self.graph
            stock_list = stocks
        else:
            graph = self.graph
            # TODO: 获取完整的股票列表
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
        # TODO: 根据股票代码获取索引
        stock_idx = 0  # 示例
        
        # 获取被影响（incoming edges）
        influenced_by_weights = self.graph[:, stock_idx]
        influenced_by_indices = np.argsort(influenced_by_weights)[-top_k:][::-1]
        
        # 获取影响（outgoing edges）
        influences_weights = self.graph[stock_idx, :]
        influences_indices = np.argsort(influences_weights)[-top_k:][::-1]
        
        return {
            'stock': stock,
            'influenced_by': [
                {'stock': f'Stock_{i}', 'weight': float(influenced_by_weights[i])}
                for i in influenced_by_indices
                if influenced_by_weights[i] > 0
            ],
            'influences': [
                {'stock': f'Stock_{i}', 'weight': float(influences_weights[i])}
                for i in influences_indices
                if influences_weights[i] > 0
            ]
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
        # TODO: 从配置中读取股票列表
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
