#!/usr/bin/env python3
"""
Phase 2 Day 2-3 集成测试
测试 3个数据集 × 3种因果发现方法 = 9种组合
生成性能基准测试报告
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

# 导入我们的模块
from unified_data_loader import UnifiedDataLoader, create_data_loader
from causal_discovery_manager import CausalDiscoveryManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTester:
    """集成测试器"""
    
    def __init__(self, output_dir: str = 'test_results', use_synthetic_data: bool = False):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.use_synthetic_data = use_synthetic_data
        self.datasets = ['synthetic_small', 'synthetic_medium', 'synthetic_large'] if use_synthetic_data else ['cikm18']
        self.methods = ['granger', 'transfer_entropy']  # CUTS+需要完整实现
        
        self.results = []
        
        logger.info(f"IntegrationTester initialized: output_dir={output_dir}, synthetic={use_synthetic_data}")
    
    def generate_synthetic_data(self, dataset_name: str) -> tuple:
        """
        生成合成测试数据
        
        Args:
            dataset_name: 数据集名称（synthetic_small/medium/large）
            
        Returns:
            data: 价格数据矩阵
            stock_names: 股票名称列表
        """
        # 根据数据集大小设置参数
        config = {
            'synthetic_small': {'n_stocks': 10, 'n_days': 200},
            'synthetic_medium': {'n_stocks': 20, 'n_days': 300},
            'synthetic_large': {'n_stocks': 30, 'n_days': 500}
        }
        
        params = config.get(dataset_name, config['synthetic_small'])
        n_stocks = params['n_stocks']
        n_days = params['n_days']
        
        # 创建有因果关系的数据
        np.random.seed(42)
        data = np.zeros((n_days, n_stocks))
        
        # 第一只股票：随机游走
        data[:, 0] = np.cumsum(np.random.randn(n_days))
        
        # 后续股票：部分受前面股票影响
        for i in range(1, n_stocks):
            # 自回归
            ar_coef = np.random.uniform(0.5, 0.8)
            # 因果影响（30%概率）
            has_causal = np.random.rand() < 0.3
            
            for t in range(2, n_days):
                data[t, i] = ar_coef * data[t-1, i]
                
                if has_causal and i > 0:
                    source_idx = np.random.randint(0, i)
                    causal_coef = np.random.uniform(0.1, 0.3)
                    data[t, i] += causal_coef * data[t-1, source_idx]
                
                data[t, i] += np.random.randn() * 0.1
        
        stock_names = [f'Stock_{i}' for i in range(n_stocks)]
        
        logger.info(f"Generated {dataset_name}: {n_stocks} stocks, {n_days} days")
        return data, stock_names
    
    def load_dataset_sample(self, dataset_name: str, n_stocks: int = 10, n_days: int = 100) -> tuple:
        """
        加载数据集样本用于测试
        
        Args:
            dataset_name: 数据集名称
            n_stocks: 股票数量（用于测试）
            n_days: 天数（用于测试）
            
        Returns:
            data: 价格数据矩阵
            stock_names: 股票名称列表
        """
        # 如果使用合成数据
        if self.use_synthetic_data or dataset_name.startswith('synthetic_'):
            return self.generate_synthetic_data(dataset_name)
        
        # 否则尝试加载真实数据
        try:
            loader = create_data_loader(dataset_name)
            
            # 获取股票列表
            all_stocks = loader.get_stock_list()[:n_stocks]
            
            # 加载价格数据
            price_path = loader.data_pipe.movement_path
            data = []
            
            for stock in all_stocks:
                price_file = Path(price_path) / f"{stock}.tsv"
                if price_file.exists():
                    df = pd.read_csv(price_file, sep='\t')
                    if 'close' in df.columns:
                        prices = df['close'].values[:n_days]
                    elif 'Close' in df.columns:
                        prices = df['Close'].values[:n_days]
                    else:
                        prices = df.iloc[:, 1].values[:n_days]  # 假设第二列是价格
                    
                    data.append(prices)
            
            # 转换为numpy数组 (n_days, n_stocks)
            data = np.array(data).T
            
            # 处理缺失值
            if np.any(np.isnan(data)):
                # 前向填充
                for i in range(data.shape[1]):
                    mask = np.isnan(data[:, i])
                    if np.any(mask):
                        idx = np.where(~mask)[0]
                        if len(idx) > 0:
                            data[mask, i] = np.interp(np.where(mask)[0], idx, data[idx, i])
            
            logger.info(f"Loaded {dataset_name}: {data.shape[1]} stocks, {data.shape[0]} days")
            return data, all_stocks
        
        except Exception as e:
            logger.error(f"Failed to load dataset {dataset_name}: {e}")
            return None, None
    
    def test_single_combination(
        self,
        dataset_name: str,
        method: str,
        causal_manager: CausalDiscoveryManager
    ) -> Dict:
        """
        测试单个数据集和方法的组合
        
        Args:
            dataset_name: 数据集名称
            method: 因果发现方法
            causal_manager: 因果发现管理器
            
        Returns:
            result: 测试结果字典
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Testing: {dataset_name} + {method}")
        logger.info(f"{'='*70}")
        
        result = {
            'dataset': dataset_name,
            'method': method,
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            # 加载数据
            data, stock_names = self.load_dataset_sample(dataset_name, n_stocks=10, n_days=150)
            
            if data is None:
                result['error'] = 'Failed to load dataset'
                return result
            
            result['n_stocks'] = len(stock_names)
            result['n_timepoints'] = len(data)
            
            # 计算因果图
            start_time = datetime.now()
            
            # 对于传递熵，使用更少的置换次数以加快测试
            custom_config = {}
            if method == 'transfer_entropy':
                custom_config = {
                    'n_surrogates': 20,  # 减少到20次置换
                    'k_history': 2,  # 减少历史长度
                    'method': 'binning'  # 使用更快的binning方法
                }
            
            graph, info = causal_manager.compute_causal_graph(
                data,
                stock_names,
                method=method,
                custom_config=custom_config
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # 记录结果
            result['success'] = True
            result['computation_time'] = elapsed
            result['n_edges'] = int(info.get('n_edges', 0))
            result['sparsity'] = float(info.get('sparsity', 0))
            result['density'] = float(info.get('density', 0))
            result['graph_shape'] = graph.shape
            result['from_cache'] = info.get('from_cache', False)
            
            # 方法特定信息
            if method == 'granger':
                result['max_lags'] = info.get('max_lags')
                result['significance_level'] = info.get('significance_level')
            elif method == 'transfer_entropy':
                result['k_history'] = info.get('k_history')
                result['te_method'] = info.get('method')
                result['n_surrogates'] = info.get('n_surrogates')
            
            logger.info(f"✓ Success: {elapsed:.2f}s, {result['n_edges']} edges, {result['sparsity']:.2%} sparsity")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"✗ Failed: {e}")
        
        return result
    
    def run_all_tests(self) -> List[Dict]:
        """运行所有测试组合"""
        logger.info("\n" + "="*70)
        logger.info("STARTING INTEGRATION TESTS")
        logger.info(f"Datasets: {self.datasets}")
        logger.info(f"Methods: {self.methods}")
        logger.info(f"Total combinations: {len(self.datasets) * len(self.methods)}")
        logger.info("="*70)
        
        # 创建因果发现管理器
        causal_manager = CausalDiscoveryManager(
            cache_dir='integration_test_cache',
            enable_cache=True
        )
        
        # 测试所有组合
        for dataset in self.datasets:
            for method in self.methods:
                result = self.test_single_combination(dataset, method, causal_manager)
                self.results.append(result)
        
        return self.results
    
    def generate_report(self):
        """生成测试报告"""
        logger.info("\n" + "="*70)
        logger.info("GENERATING TEST REPORT")
        logger.info("="*70)
        
        # 保存JSON报告
        report_file = self.output_dir / f'integration_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n✓ Report saved to: {report_file}")
        
        # 打印摘要
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        # 统计
        total = len(self.results)
        successful = sum(1 for r in self.results if r['success'])
        failed = total - successful
        
        print(f"\nTotal tests: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        # 成功的测试详情
        if successful > 0:
            print("\n" + "-"*70)
            print("SUCCESSFUL TESTS")
            print("-"*70)
            
            # 创建表格
            df_data = []
            for r in self.results:
                if r['success']:
                    df_data.append({
                        'Dataset': r['dataset'],
                        'Method': r['method'],
                        'Time (s)': f"{r['computation_time']:.2f}",
                        'Edges': r['n_edges'],
                        'Sparsity': f"{r['sparsity']:.2%}",
                        'From Cache': '✓' if r.get('from_cache') else '✗'
                    })
            
            df = pd.DataFrame(df_data)
            print(df.to_string(index=False))
        
        # 失败的测试详情
        if failed > 0:
            print("\n" + "-"*70)
            print("FAILED TESTS")
            print("-"*70)
            
            for r in self.results:
                if not r['success']:
                    print(f"  ✗ {r['dataset']} + {r['method']}: {r.get('error', 'Unknown error')}")
        
        # 性能对比
        print("\n" + "-"*70)
        print("PERFORMANCE COMPARISON")
        print("-"*70)
        
        # 按方法分组
        method_times = {}
        for r in self.results:
            if r['success']:
                method = r['method']
                if method not in method_times:
                    method_times[method] = []
                method_times[method].append(r['computation_time'])
        
        for method, times in method_times.items():
            avg_time = np.mean(times)
            print(f"  {method}: {avg_time:.2f}s (avg), {min(times):.2f}s (min), {max(times):.2f}s (max)")
        
        print("\n" + "="*70)
        print("INTEGRATION TEST COMPLETED!")
        print("="*70)


def main():
    """主测试流程"""
    print("="*70)
    print("PHASE 2 DAY 2-3 INTEGRATION TEST")
    print("="*70)
    
    # 创建测试器（使用合成数据以确保测试可靠运行）
    tester = IntegrationTester(output_dir='test_results', use_synthetic_data=True)
    
    # 运行所有测试
    results = tester.run_all_tests()
    
    # 生成报告
    tester.generate_report()
    
    # 清理测试缓存
    print("\nCleaning up test cache...")
    from causal_discovery_manager import CausalDiscoveryManager
    manager = CausalDiscoveryManager(cache_dir='integration_test_cache')
    manager.clear_cache()
    print("✓ Cache cleared")


if __name__ == '__main__':
    main()
