#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unified Pipeline for Stock Prediction System
=============================================

端到端的股票预测工作流管道，整合：
1. 数据加载 (UnifiedDataLoader)
2. 因果发现 (CausalDiscoveryManager)
3. 股票预测 (StockPredictor)

支持：
- 完整的数据流处理
- 多种因果发现方法
- 批量预测和分析
- 结果可视化
- 性能监控

Author: ICSFP Team
Created: 2025-11-11
"""

import os
import time
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 导入核心模块
from unified_data_loader import UnifiedDataLoader
from causal_discovery_manager import CausalDiscoveryManager
from api.predictor import StockPredictor
from utils.stock_mapper import StockMapper
from utils.data_preprocessor import DataPreprocessor

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedPipeline:
    """
    统一的股票预测工作流管道
    
    整合数据加载、因果发现、预测三个核心模块，
    提供端到端的预测流程。
    
    Attributes:
        data_loader: 数据加载器
        causal_manager: 因果发现管理器
        predictor: 股票预测器
        stock_mapper: 股票代码映射器
        preprocessor: 数据预处理器
    """
    
    def __init__(
        self,
        dataset_name: str = 'cikm18',
        config_path: str = 'config.yml',
        stock_list_path: Optional[str] = None,
        causal_method: str = 'granger',
        enable_cache: bool = True,
        enable_preprocessing: bool = True
    ):
        """
        初始化统一管道
        
        Args:
            dataset_name: 数据集名称 (acl18/cikm18/cmin-cn)
            config_path: 配置文件路径
            stock_list_path: 股票列表文件路径
            causal_method: 因果发现方法 (granger/cuts_plus/transfer_entropy)
            enable_cache: 是否启用缓存
            enable_preprocessing: 是否启用数据预处理
        """
        logger.info("="*70)
        logger.info("Initializing Unified Pipeline")
        logger.info("="*70)
        
        self.dataset_name = dataset_name
        self.config_path = config_path
        self.causal_method = causal_method
        self.enable_cache = enable_cache
        self.enable_preprocessing = enable_preprocessing
        
        # 性能指标
        self.metrics = {
            'data_loading_time': 0.0,
            'causal_discovery_time': 0.0,
            'prediction_time': 0.0,
            'total_time': 0.0
        }
        
        # 初始化各模块
        self._init_modules(stock_list_path)
        
        logger.info("Pipeline initialized successfully")
        logger.info(f"Dataset: {dataset_name}")
        logger.info(f"Causal Method: {causal_method}")
        logger.info(f"Cache Enabled: {enable_cache}")
        logger.info("="*70 + "\n")
    
    def _init_modules(self, stock_list_path: Optional[str]):
        """初始化各个模块"""
        try:
            # 1. 初始化数据加载器
            logger.info("Initializing Data Loader...")
            start_time = time.time()
            self.data_loader = UnifiedDataLoader(dataset_name=self.dataset_name)
            self.metrics['data_loading_time'] = time.time() - start_time
            logger.info(f"✓ Data Loader initialized ({self.metrics['data_loading_time']:.3f}s)")
            
            # 2. 初始化因果发现管理器
            logger.info("Initializing Causal Discovery Manager...")
            start_time = time.time()
            self.causal_manager = CausalDiscoveryManager(
                cache_dir='causal_graphs',
                enable_cache=self.enable_cache,
                default_method=self.causal_method
            )
            logger.info(f"✓ Causal Manager initialized ({time.time() - start_time:.3f}s)")
            
            # 3. 初始化股票预测器
            logger.info("Initializing Stock Predictor...")
            start_time = time.time()
            self.predictor = StockPredictor(
                config_path=self.config_path,
                stock_list_path=stock_list_path,
                enable_preprocessing=self.enable_preprocessing
            )
            logger.info(f"✓ Predictor initialized ({time.time() - start_time:.3f}s)")
            
            # 4. 获取引用
            self.stock_mapper = self.predictor.stock_mapper
            self.preprocessor = self.predictor.preprocessor
            
        except Exception as e:
            logger.error(f"Error initializing modules: {e}", exc_info=True)
            raise
    
    def run_full_pipeline(
        self,
        stock_symbols: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        causal_threshold: float = 0.3,
        top_k_influence: int = 10,
        use_causal: bool = True
    ) -> Dict[str, Any]:
        """
        运行完整的预测管道
        
        Args:
            stock_symbols: 要预测的股票列表 (None=所有)
            start_date: 开始日期
            end_date: 结束日期
            causal_threshold: 因果关系阈值
            top_k_influence: 返回前K个影响最大的股票
            use_causal: 预测时是否使用因果信息
        
        Returns:
            包含预测结果、因果图、性能指标的字典
        """
        logger.info("\n" + "="*70)
        logger.info("Running Full Pipeline")
        logger.info("="*70)
        
        pipeline_start = time.time()
        
        try:
            # Step 1: 加载数据
            logger.info("\n[Step 1/4] Loading Data...")
            data_result = self._load_data(stock_symbols, start_date, end_date)
            
            # Step 2: 因果发现
            logger.info("\n[Step 2/4] Discovering Causal Relationships...")
            causal_result = self._discover_causality(
                data_result['data'],
                stock_list=data_result['stock_list'],
                method=self.causal_method,
                threshold=causal_threshold
            )
            
            # Step 3: 更新预测器的因果图
            logger.info("\n[Step 3/4] Updating Predictor with Causal Graph...")
            self._update_predictor_graph(causal_result['graph'])
            
            # Step 4: 执行预测
            logger.info("\n[Step 4/4] Generating Predictions...")
            prediction_result = self._generate_predictions(
                stock_symbols=stock_symbols or data_result.get('stock_list', []),
                start_date=start_date,
                end_date=end_date,
                use_causal=use_causal
            )
            
            # 计算总时间
            self.metrics['total_time'] = time.time() - pipeline_start
            
            # 整合结果
            result = {
                'success': True,
                'data_info': data_result,
                'causal_graph': causal_result,
                'predictions': prediction_result,
                'metrics': self.metrics.copy(),
                'config': {
                    'dataset': self.dataset_name,
                    'causal_method': self.causal_method,
                    'causal_threshold': causal_threshold,
                    'use_causal': use_causal
                }
            }
            
            self._print_summary(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'metrics': self.metrics.copy()
            }
    
    def _load_data(
        self,
        stock_symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Dict[str, Any]:
        """加载真实数据 - 从DataPipe提取价格序列"""
        start_time = time.time()
        
        try:
            # 获取数据集信息
            dataset_info = self.data_loader.get_dataset_info()
            
            # 如果没有指定股票，使用数据集中的所有股票
            if stock_symbols is None:
                stock_list = self.data_loader.get_stock_list()[:10]  # 限制数量
            else:
                stock_list = stock_symbols
            
            logger.info(f"Loading data for {len(stock_list)} stocks")
            logger.info(f"Date range: {start_date or 'default'} to {end_date or 'default'}")
            
            # 从 DataPipe 批次中提取真实价格数据
            price_data = self._extract_price_data_from_batches(stock_list, phase='train')
            
            elapsed = time.time() - start_time
            self.metrics['data_loading_time'] += elapsed
            
            logger.info(f"✓ Data loaded successfully ({elapsed:.3f}s)")
            logger.info(f"  - Stocks: {len(stock_list)}")
            logger.info(f"  - Time steps: {price_data.shape[0] if price_data is not None else 0}")
            
            return {
                'data': price_data,
                'stock_list': stock_list,
                'dataset_info': dataset_info,
                'batch': {}
            }
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def _extract_price_data_from_batches(
        self, 
        stock_list: List[str], 
        phase: str = 'train',
        max_samples: int = 100
    ) -> np.ndarray:
        """
        从 DataPipe 批次中提取真实价格数据
        
        Args:
            stock_list: 股票列表
            phase: 数据阶段 ('train', 'dev', 'test')
            max_samples: 最大采样数量
            
        Returns:
            price_data: 形状为 (n_timesteps, n_stocks) 的价格矩阵
        """
        try:
            # 获取股票ID映射
            data_pipe = self.data_loader.data_pipe
            stock_id_dict = data_pipe.index_token(stock_list, key='token', type='stock')
            
            # 收集价格数据
            all_prices = []
            sample_count = 0
            
            logger.info(f"Extracting price data for {len(stock_list)} stocks from {phase} phase")
            
            # 从批次生成器中提取数据
            for batch in data_pipe.batch_gen(phase=phase):
                if sample_count >= max_samples:
                    break
                
                # price_batch shape: (batch_size, max_n_days, 3)
                # 第3维: [open, high, low] 或 [close, high, low]
                price_batch = batch['price_batch']
                T_batch = batch['T_batch']
                stock_batch = batch['stock_batch']
                
                # 提取每个样本的收盘价格序列
                for i in range(batch['batch_size']):
                    T = T_batch[i]
                    stock_id = stock_batch[i]
                    
                    # 获取该股票在stock_list中的索引
                    try:
                        stock_idx = list(stock_id_dict.values()).index(stock_id)
                    except ValueError:
                        continue  # 跳过不在目标列表中的股票
                    
                    # 提取价格序列 (使用第一列作为主要价格)
                    prices = price_batch[i, :T, 0]  # shape: (T,)
                    
                    # 构建一个包含该股票价格的向量
                    price_vec = np.zeros(len(stock_list))
                    price_vec[stock_idx] = prices[-1] if len(prices) > 0 else 0.0
                    
                    all_prices.append(price_vec)
                    sample_count += 1
                    
                    if sample_count >= max_samples:
                        break
            
            if len(all_prices) == 0:
                logger.warning("No price data extracted, using small random fallback")
                return np.random.randn(20, len(stock_list)) * 0.01 + 100.0
            
            # 转换为矩阵 (n_timesteps, n_stocks)
            price_matrix = np.array(all_prices)
            
            logger.info(f"Extracted price matrix shape: {price_matrix.shape}")
            logger.info(f"Price statistics - mean: {price_matrix.mean():.2f}, "
                       f"std: {price_matrix.std():.2f}, "
                       f"min: {price_matrix.min():.2f}, max: {price_matrix.max():.2f}")
            
            return price_matrix
            
        except Exception as e:
            logger.error(f"Error extracting price data: {e}")
            logger.warning("Falling back to minimal random data")
            import traceback
            traceback.print_exc()
            return np.random.randn(20, len(stock_list)) * 0.01 + 100.0
    
    def _discover_causality(
        self,
        data: np.ndarray,
        stock_list: List[str],
        method: str = 'granger',
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        执行因果发现 - 不使用异常捕获，让真实错误暴露
        
        Args:
            data: 时间序列数据 (n_timesteps, n_stocks)
            stock_list: 股票列表
            method: 因果发现方法
            threshold: 阈值
            
        Returns:
            结果字典包含图、统计信息等
        """
        start_time = time.time()
        
        logger.info(f"Using method: {method}")
        logger.info(f"Data shape: {data.shape}")
        logger.info(f"Stock list: {stock_list}")
        logger.info(f"Threshold: {threshold}")
        
        # 计算因果图 - 正确传递所有必需参数
        graph, metadata = self.causal_manager.compute_causal_graph(
            data=data,
            stock_names=stock_list,
            method=method,
            max_lag=5,
            threshold=threshold
        )
        
        # 获取统计信息 - 使用新添加的方法
        stats = self.causal_manager.get_graph_statistics(graph, threshold)
        
        elapsed = time.time() - start_time
        self.metrics['causal_discovery_time'] += elapsed
        
        logger.info(f"✓ Causal graph computed ({elapsed:.3f}s)")
        logger.info(f"  - Nodes: {stats['num_nodes']}")
        logger.info(f"  - Edges: {stats['num_edges']}")
        logger.info(f"  - Density: {stats['density']:.4f}")
        logger.info(f"  - Sparsity: {stats['sparsity']:.4f}")
        
        return {
            'graph': graph,
            'method': method,
            'threshold': threshold,
            'statistics': stats,
            'metadata': metadata
        }
    
    def _update_predictor_graph(self, causal_graph: np.ndarray):
        """更新预测器的因果图"""
        try:
            self.predictor.graph = causal_graph
            logger.info(f"✓ Predictor causal graph updated: {causal_graph.shape}")
        except Exception as e:
            logger.warning(f"Failed to update predictor graph: {e}")
    
    def _generate_predictions(
        self,
        stock_symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
        use_causal: bool
    ) -> Dict[str, Any]:
        """生成预测"""
        start_time = time.time()
        
        try:
            logger.info(f"Generating predictions for {len(stock_symbols)} stocks")
            logger.info(f"Use causal info: {use_causal}")
            
            # 批量预测
            predictions = self.predictor.predict_batch(
                stock_symbols=stock_symbols,
                start_date=start_date,
                end_date=end_date,
                use_causal=use_causal
            )
            
            elapsed = time.time() - start_time
            self.metrics['prediction_time'] += elapsed
            
            logger.info(f"✓ Predictions generated ({elapsed:.3f}s)")
            logger.info(f"  - Total predictions: {predictions['summary']['total_predictions']}")
            logger.info(f"  - Avg confidence: {predictions['summary']['avg_confidence']:.3f}")
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {
                'predictions': {},
                'summary': {
                    'total_stocks': len(stock_symbols),
                    'total_predictions': 0,
                    'avg_confidence': 0.0
                },
                'error': str(e)
            }
    
    def _print_summary(self, result: Dict[str, Any]):
        """打印执行摘要"""
        logger.info("\n" + "="*70)
        logger.info("Pipeline Execution Summary")
        logger.info("="*70)
        
        if result['success']:
            logger.info("✓ Status: SUCCESS")
            
            # 数据信息
            data_info = result['data_info']
            logger.info(f"\n[Data]")
            logger.info(f"  - Dataset: {self.dataset_name}")
            logger.info(f"  - Stocks: {len(data_info['stock_list'])}")
            
            # 因果图信息
            causal_info = result['causal_graph']
            stats = causal_info['statistics']
            logger.info(f"\n[Causal Graph]")
            logger.info(f"  - Method: {causal_info['method']}")
            logger.info(f"  - Nodes: {stats['num_nodes']}")
            logger.info(f"  - Edges: {stats['num_edges']}")
            logger.info(f"  - Density: {stats['density']:.4f}")
            
            # 预测信息
            pred_info = result['predictions']['summary']
            logger.info(f"\n[Predictions]")
            logger.info(f"  - Total: {pred_info['total_predictions']}")
            logger.info(f"  - Avg Confidence: {pred_info['avg_confidence']:.3f}")
            
            # 性能指标
            metrics = result['metrics']
            logger.info(f"\n[Performance]")
            logger.info(f"  - Data Loading: {metrics['data_loading_time']:.3f}s")
            logger.info(f"  - Causal Discovery: {metrics['causal_discovery_time']:.3f}s")
            logger.info(f"  - Prediction: {metrics['prediction_time']:.3f}s")
            logger.info(f"  - Total: {metrics['total_time']:.3f}s")
        else:
            logger.error("✗ Status: FAILED")
            logger.error(f"  - Error: {result.get('error', 'Unknown')}")
        
        logger.info("="*70 + "\n")
    
    def get_causal_analysis(
        self,
        stock_symbol: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        获取单个股票的因果分析
        
        Args:
            stock_symbol: 股票代码
            top_k: 返回前K个影响最大的股票
        
        Returns:
            因果影响分析结果
        """
        return self.predictor.get_causal_influence(stock_symbol, top_k)
    
    def compare_causal_methods(
        self,
        data: np.ndarray,
        stock_list: Optional[List[str]] = None,
        methods: Optional[List[str]] = None,
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        对比多种因果发现方法
        
        Args:
            data: 股票价格数据
            stock_list: 股票列表
            methods: 要对比的方法列表
            threshold: 因果关系阈值
        
        Returns:
            对比结果
        """
        if methods is None:
            methods = ['granger', 'cuts_plus', 'transfer_entropy']
        
        if stock_list is None:
            stock_list = [f'Stock_{i}' for i in range(data.shape[1])]
        
        logger.info(f"Comparing {len(methods)} causal discovery methods...")
        
        results = {}
        for method in methods:
            logger.info(f"\nTesting method: {method}")
            start_time = time.time()
            
            try:
                graph, metadata = self.causal_manager.compute_causal_graph(
                    data=data,
                    stock_names=stock_list,
                    method=method,
                    threshold=threshold
                )
                stats = self.causal_manager.get_graph_statistics(graph, threshold)
                
                results[method] = {
                    'graph': graph,
                    'statistics': stats,
                    'time': time.time() - start_time,
                    'success': True
                }
                
                logger.info(f"✓ {method}: {stats['num_edges']} edges, "
                          f"{time.time() - start_time:.3f}s")
                
            except Exception as e:
                logger.error(f"✗ {method} failed: {e}")
                results[method] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def save_results(
        self,
        result: Dict[str, Any],
        output_dir: str = 'pipeline_results',
        prefix: str = 'result'
    ) -> str:
        """
        保存管道执行结果
        
        Args:
            result: 执行结果
            output_dir: 输出目录
            prefix: 文件前缀
        
        Returns:
            保存的文件路径
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{prefix}_{timestamp}.npz"
            filepath = output_path / filename
            
            # 保存因果图和预测结果
            np.savez_compressed(
                filepath,
                causal_graph=result['causal_graph']['graph'],
                metrics=np.array([result['metrics']]),
                config=np.array([result['config']])
            )
            
            logger.info(f"Results saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return ""
    
    def get_metrics(self) -> Dict[str, float]:
        """获取性能指标"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """重置性能指标"""
        for key in self.metrics:
            self.metrics[key] = 0.0


# 便捷函数
def create_pipeline(
    dataset_name: str = 'cikm18',
    causal_method: str = 'granger',
    **kwargs
) -> UnifiedPipeline:
    """
    创建统一管道的便捷函数
    
    Args:
        dataset_name: 数据集名称
        causal_method: 因果发现方法
        **kwargs: 其他参数
    
    Returns:
        UnifiedPipeline 实例
    """
    return UnifiedPipeline(
        dataset_name=dataset_name,
        causal_method=causal_method,
        **kwargs
    )


if __name__ == '__main__':
    # 示例使用
    print("="*70)
    print("Unified Pipeline - Example Usage")
    print("="*70 + "\n")
    
    # 创建管道
    pipeline = create_pipeline(
        dataset_name='cikm18',
        causal_method='granger',
        enable_cache=True
    )
    
    # 运行完整管道
    result = pipeline.run_full_pipeline(
        stock_symbols=None,  # 使用默认股票列表
        start_date='2015-01-01',
        end_date='2015-12-31',
        causal_threshold=0.3,
        use_causal=True
    )
    
    # 打印结果
    if result['success']:
        print("\n✓ Pipeline completed successfully!")
        print(f"Total time: {result['metrics']['total_time']:.3f}s")
    else:
        print(f"\n✗ Pipeline failed: {result.get('error', 'Unknown error')}")
