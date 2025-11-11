"""
测试统一管道 (Unified Pipeline)
测试端到端的数据加载、因果发现、预测流程
"""

import os
import sys
import unittest
import numpy as np
import tempfile
import json
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unified_pipeline import UnifiedPipeline, create_pipeline


class TestUnifiedPipeline(unittest.TestCase):
    """测试统一管道"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.temp_dir = tempfile.mkdtemp()
        
        # 创建测试股票列表
        cls.stock_list_file = os.path.join(cls.temp_dir, 'stocks.json')
        stocks = [
            {'code': f'Stock_{i:03d}', 'index': i, 'name': f'Stock {i}', 'sector': 'default'}
            for i in range(10)
        ]
        with open(cls.stock_list_file, 'w') as f:
            json.dump(stocks, f)
        
        print(f"\nTest environment created in {cls.temp_dir}")
    
    def test_1_pipeline_initialization(self):
        """测试管道初始化"""
        print("\n" + "="*70)
        print("Test 1: Pipeline Initialization")
        print("="*70)
        
        try:
            pipeline = UnifiedPipeline(
                dataset_name='cikm18',
                causal_method='granger',
                stock_list_path=self.stock_list_file,
                enable_cache=False
            )
            
            self.assertIsNotNone(pipeline.data_loader)
            self.assertIsNotNone(pipeline.causal_manager)
            self.assertIsNotNone(pipeline.predictor)
            
            print("✓ Pipeline initialized successfully")
            print(f"  - Data Loader: OK")
            print(f"  - Causal Manager: OK")
            print(f"  - Predictor: OK")
            
        except Exception as e:
            print(f"✗ Initialization failed: {e}")
            raise
    
    def test_2_load_data(self):
        """测试数据加载"""
        print("\n" + "="*70)
        print("Test 2: Data Loading")
        print("="*70)
        
        pipeline = UnifiedPipeline(
            dataset_name='cikm18',
            stock_list_path=self.stock_list_file,
            enable_cache=False
        )
        
        stock_symbols = [f'Stock_{i:03d}' for i in range(5)]
        data_result = pipeline._load_data(
            stock_symbols=stock_symbols,
            start_date='2015-01-01',
            end_date='2015-01-10'
        )
        
        self.assertIn('data', data_result)
        self.assertIn('stock_list', data_result)
        self.assertIsNotNone(data_result['data'])
        
        print("✓ Data loaded successfully")
        print(f"  - Data shape: {data_result['data'].shape}")
        print(f"  - Stocks: {len(data_result['stock_list'])}")
    
    def test_3_causal_discovery(self):
        """测试因果发现"""
        print("\n" + "="*70)
        print("Test 3: Causal Discovery")
        print("="*70)
        
        pipeline = UnifiedPipeline(
            dataset_name='cikm18',
            causal_method='granger',
            enable_cache=False
        )
        
        # 生成模拟数据
        mock_data = np.random.randn(20, 10) * 0.02 + 100.0
        stock_list = [f'Stock_{i:03d}' for i in range(10)]
        
        causal_result = pipeline._discover_causality(
            data=mock_data,
            stock_list=stock_list,
            method='granger',
            threshold=0.3
        )
        
        self.assertIn('graph', causal_result)
        self.assertIn('statistics', causal_result)
        self.assertEqual(causal_result['graph'].shape, (10, 10))
        
        stats = causal_result['statistics']
        print("✓ Causal discovery completed")
        print(f"  - Graph shape: {causal_result['graph'].shape}")
        print(f"  - Edges: {stats['num_edges']}")
        print(f"  - Density: {stats['density']:.4f}")
    
    def test_4_prediction(self):
        """测试预测生成"""
        print("\n" + "="*70)
        print("Test 4: Prediction Generation")
        print("="*70)
        
        pipeline = UnifiedPipeline(
            dataset_name='cikm18',
            stock_list_path=self.stock_list_file,
            enable_cache=False
        )
        
        stock_symbols = [f'Stock_{i:03d}' for i in range(3)]
        pred_result = pipeline._generate_predictions(
            stock_symbols=stock_symbols,
            start_date='2015-01-01',
            end_date='2015-01-10',
            use_causal=True
        )
        
        self.assertIn('predictions', pred_result)
        self.assertIn('summary', pred_result)
        
        summary = pred_result['summary']
        print("✓ Predictions generated")
        print(f"  - Total stocks: {summary['total_stocks']}")
        print(f"  - Total predictions: {summary['total_predictions']}")
        print(f"  - Avg confidence: {summary['avg_confidence']:.3f}")
    
    def test_5_full_pipeline(self):
        """测试完整管道"""
        print("\n" + "="*70)
        print("Test 5: Full Pipeline Execution")
        print("="*70)
        
        pipeline = UnifiedPipeline(
            dataset_name='cikm18',
            causal_method='granger',
            stock_list_path=self.stock_list_file,
            enable_cache=False
        )
        
        stock_symbols = [f'Stock_{i:03d}' for i in range(5)]
        
        result = pipeline.run_full_pipeline(
            stock_symbols=stock_symbols,
            start_date='2015-01-01',
            end_date='2015-01-10',
            causal_threshold=0.3,
            use_causal=True
        )
        
        self.assertTrue(result['success'])
        self.assertIn('data_info', result)
        self.assertIn('causal_graph', result)
        self.assertIn('predictions', result)
        self.assertIn('metrics', result)
        
        metrics = result['metrics']
        print("✓ Full pipeline completed")
        print(f"  - Data loading time: {metrics['data_loading_time']:.3f}s")
        print(f"  - Causal discovery time: {metrics['causal_discovery_time']:.3f}s")
        print(f"  - Prediction time: {metrics['prediction_time']:.3f}s")
        print(f"  - Total time: {metrics['total_time']:.3f}s")
    
    def test_6_causal_analysis(self):
        """测试因果分析"""
        print("\n" + "="*70)
        print("Test 6: Causal Analysis")
        print("="*70)
        
        pipeline = UnifiedPipeline(
            dataset_name='cikm18',
            stock_list_path=self.stock_list_file,
            enable_cache=False
        )
        
        # 先运行管道以生成因果图
        stock_symbols = [f'Stock_{i:03d}' for i in range(5)]
        pipeline.run_full_pipeline(
            stock_symbols=stock_symbols,
            causal_threshold=0.3
        )
        
        # 获取因果分析
        analysis = pipeline.get_causal_analysis(
            stock_symbol='Stock_000',
            top_k=3
        )
        
        self.assertIn('stock', analysis)
        self.assertIn('influenced_by', analysis)
        self.assertIn('influences', analysis)
        
        print("✓ Causal analysis retrieved")
        print(f"  - Target stock: {analysis['stock']}")
        print(f"  - Influenced by: {len(analysis['influenced_by'])}")
        print(f"  - Influences: {len(analysis['influences'])}")
    
    def test_7_method_comparison(self):
        """测试方法对比"""
        print("\n" + "="*70)
        print("Test 7: Method Comparison")
        print("="*70)
        
        pipeline = UnifiedPipeline(
            dataset_name='cikm18',
            enable_cache=False
        )
        
        # 生成模拟数据
        mock_data = np.random.randn(20, 8) * 0.02 + 100.0
        stock_list = [f'Stock_{i}' for i in range(8)]
        
        # 对比方法（只测试快速方法）
        results = pipeline.compare_causal_methods(
            data=mock_data,
            stock_list=stock_list,
            methods=['granger', 'cuts_plus'],
            threshold=0.3
        )
        
        self.assertIn('granger', results)
        self.assertIn('cuts_plus', results)
        
        print("✓ Method comparison completed")
        for method, result in results.items():
            if result.get('success', False):
                print(f"  - {method}: {result['statistics']['num_edges']} edges, "
                      f"{result['time']:.3f}s")
            else:
                print(f"  - {method}: FAILED")
    
    def test_8_metrics_tracking(self):
        """测试性能指标跟踪"""
        print("\n" + "="*70)
        print("Test 8: Metrics Tracking")
        print("="*70)
        
        pipeline = UnifiedPipeline(
            dataset_name='cikm18',
            enable_cache=False
        )
        
        # 获取初始指标
        initial_metrics = pipeline.get_metrics()
        self.assertEqual(initial_metrics['total_time'], 0.0)
        
        # 运行管道
        stock_symbols = [f'Stock_{i:03d}' for i in range(3)]
        pipeline.run_full_pipeline(
            stock_symbols=stock_symbols,
            causal_threshold=0.3
        )
        
        # 获取更新后的指标
        updated_metrics = pipeline.get_metrics()
        self.assertGreater(updated_metrics['total_time'], 0.0)
        
        print("✓ Metrics tracked successfully")
        print(f"  - Data loading: {updated_metrics['data_loading_time']:.3f}s")
        print(f"  - Causal discovery: {updated_metrics['causal_discovery_time']:.3f}s")
        print(f"  - Prediction: {updated_metrics['prediction_time']:.3f}s")
        print(f"  - Total: {updated_metrics['total_time']:.3f}s")
        
        # 重置指标
        pipeline.reset_metrics()
        reset_metrics = pipeline.get_metrics()
        self.assertEqual(reset_metrics['total_time'], 0.0)
        print("✓ Metrics reset successfully")
    
    def test_9_save_results(self):
        """测试结果保存"""
        print("\n" + "="*70)
        print("Test 9: Save Results")
        print("="*70)
        
        pipeline = UnifiedPipeline(
            dataset_name='cikm18',
            stock_list_path=self.stock_list_file,
            enable_cache=False
        )
        
        # 运行管道
        result = pipeline.run_full_pipeline(
            stock_symbols=[f'Stock_{i:03d}' for i in range(3)],
            causal_threshold=0.3
        )
        
        # 保存结果
        output_dir = os.path.join(self.temp_dir, 'results')
        filepath = pipeline.save_results(
            result,
            output_dir=output_dir,
            prefix='test'
        )
        
        self.assertTrue(os.path.exists(filepath))
        
        print("✓ Results saved successfully")
        print(f"  - File: {filepath}")
    
    def test_10_create_pipeline_helper(self):
        """测试便捷创建函数"""
        print("\n" + "="*70)
        print("Test 10: Create Pipeline Helper")
        print("="*70)
        
        pipeline = create_pipeline(
            dataset_name='cikm18',
            causal_method='granger',
            stock_list_path=self.stock_list_file,
            enable_cache=False
        )
        
        self.assertIsInstance(pipeline, UnifiedPipeline)
        self.assertEqual(pipeline.dataset_name, 'cikm18')
        self.assertEqual(pipeline.causal_method, 'granger')
        
        print("✓ Pipeline created via helper function")
        print(f"  - Dataset: {pipeline.dataset_name}")
        print(f"  - Causal method: {pipeline.causal_method}")


def run_tests():
    """运行测试套件"""
    print("\n" + "="*70)
    print("测试统一管道 (Unified Pipeline)")
    print("="*70 + "\n")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestUnifiedPipeline)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print(f"测试完成: {result.testsRun} 个测试")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
