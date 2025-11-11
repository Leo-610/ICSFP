"""
测试 Predictor 集成 StockMapper 和 DataPreprocessor
"""

import os
import sys
import unittest
import numpy as np
import tempfile
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.predictor import StockPredictor
from utils.stock_mapper import StockMapper
from utils.data_preprocessor import DataPreprocessor


class TestPredictorIntegration(unittest.TestCase):
    """测试 Predictor 与新工具的集成"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 创建临时股票列表文件
        cls.temp_dir = tempfile.mkdtemp()
        cls.stock_list_file = os.path.join(cls.temp_dir, 'stocks.json')
        
        # 创建测试股票列表
        stocks = [
            {'code': 'AAPL', 'index': 0, 'name': 'Apple Inc.', 'sector': 'tech'},
            {'code': 'GOOG', 'index': 1, 'name': 'Alphabet Inc.', 'sector': 'tech'},
            {'code': 'MSFT', 'index': 2, 'name': 'Microsoft Corp.', 'sector': 'tech'},
            {'code': 'JPM', 'index': 3, 'name': 'JPMorgan Chase', 'sector': 'finance'},
            {'code': 'BAC', 'index': 4, 'name': 'Bank of America', 'sector': 'finance'}
        ]
        
        with open(cls.stock_list_file, 'w') as f:
            json.dump(stocks, f)
        
        # 创建临时因果图
        cls.causal_graph_file = os.path.join(cls.temp_dir, 'causal_graph.npy')
        graph = np.random.random((5, 5)) * 0.5
        np.fill_diagonal(graph, 0.0)
        np.save(cls.causal_graph_file, graph)
        
        print(f"Created test files in {cls.temp_dir}")
    
    def test_1_predictor_initialization(self):
        """测试 Predictor 初始化"""
        try:
            predictor = StockPredictor(
                config_path='config.yml',
                stock_list_path=self.stock_list_file
            )
            
            self.assertIsNotNone(predictor.stock_mapper)
            self.assertEqual(predictor.stock_mapper.size(), 5)
            
            self.assertIsNotNone(predictor.preprocessor)
            
            print("✓ Predictor 初始化成功")
            print(f"  - 股票数量: {predictor.stock_mapper.size()}")
            print(f"  - 预处理器状态: {'启用' if predictor.preprocessor else '禁用'}")
            
        except Exception as e:
            print(f"✗ Predictor 初始化失败: {e}")
            raise
    
    def test_2_predict_single_with_mapper(self):
        """测试单股票预测（使用 StockMapper）"""
        predictor = StockPredictor(
            config_path='config.yml',
            stock_list_path=self.stock_list_file
        )
        
        result = predictor.predict_single(
            stock_symbol='AAPL',
            start_date='2015-01-01',
            end_date='2015-01-10',
            use_causal=True
        )
        
        self.assertIn('stock_symbol', result)
        self.assertEqual(result['stock_symbol'], 'AAPL')
        self.assertIn('predictions', result)
        self.assertGreater(len(result['predictions']), 0)
        
        prediction = result['predictions'][0]
        self.assertIn('predicted_direction', prediction)
        self.assertIn(prediction['predicted_direction'], ['UP', 'DOWN'])
        self.assertIn('confidence', prediction)
        self.assertGreaterEqual(prediction['confidence'], 0.0)
        self.assertLessEqual(prediction['confidence'], 1.0)
        
        print("✓ 单股票预测成功")
        print(f"  - 股票: {result['stock_symbol']}")
        print(f"  - 预测方向: {prediction['predicted_direction']}")
        print(f"  - 置信度: {prediction['confidence']:.3f}")
    
    def test_3_predict_batch(self):
        """测试批量预测"""
        predictor = StockPredictor(
            config_path='config.yml',
            stock_list_path=self.stock_list_file
        )
        
        stocks = ['AAPL', 'GOOG', 'MSFT']
        result = predictor.predict_batch(
            stock_symbols=stocks,
            start_date='2015-01-01',
            end_date='2015-01-10',
            use_causal=True
        )
        
        self.assertIn('predictions', result)
        self.assertIn('summary', result)
        
        for stock in stocks:
            self.assertIn(stock, result['predictions'])
        
        summary = result['summary']
        self.assertEqual(summary['total_stocks'], len(stocks))
        self.assertGreaterEqual(summary['avg_confidence'], 0.0)
        
        print("✓ 批量预测成功")
        print(f"  - 股票数量: {summary['total_stocks']}")
        print(f"  - 平均置信度: {summary['avg_confidence']:.3f}")
    
    def test_4_get_causal_graph_with_mapper(self):
        """测试因果图获取（使用 StockMapper）"""
        # 切换到临时目录以使用测试因果图
        original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            predictor = StockPredictor(
                config_path='config.yml' if os.path.exists('config.yml') else os.path.join(original_dir, 'config.yml'),
                stock_list_path=self.stock_list_file
            )
            
            # 获取子图
            result = predictor.get_causal_graph(
                stocks=['AAPL', 'GOOG'],
                threshold=0.1
            )
            
            self.assertIn('graph', result)
            self.assertIn('edges', result)
            self.assertIn('stocks', result)
            self.assertEqual(len(result['stocks']), 2)
            
            print("✓ 因果图获取成功")
            print(f"  - 股票数量: {len(result['stocks'])}")
            print(f"  - 边数量: {len(result['edges'])}")
            
        finally:
            os.chdir(original_dir)
    
    def test_5_get_causal_influence_with_mapper(self):
        """测试因果影响分析（使用 StockMapper）"""
        # 切换到临时目录
        original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            predictor = StockPredictor(
                config_path='config.yml' if os.path.exists('config.yml') else os.path.join(original_dir, 'config.yml'),
                stock_list_path=self.stock_list_file
            )
            
            result = predictor.get_causal_influence(
                stock='AAPL',
                top_k=3
            )
            
            self.assertEqual(result['stock'], 'AAPL')
            self.assertIn('influenced_by', result)
            self.assertIn('influences', result)
            
            # 验证返回的是股票代码而非索引
            if result['influenced_by']:
                first_influence = result['influenced_by'][0]
                self.assertIn('stock', first_influence)
                self.assertNotRegex(first_influence['stock'], r'^Stock_\d+$')
            
            print("✓ 因果影响分析成功")
            print(f"  - 目标股票: {result['stock']}")
            print(f"  - 被影响数量: {len(result['influenced_by'])}")
            print(f"  - 影响数量: {len(result['influences'])}")
            
        finally:
            os.chdir(original_dir)
    
    def test_6_get_available_stocks_with_mapper(self):
        """测试获取可用股票列表（使用 StockMapper）"""
        predictor = StockPredictor(
            config_path='config.yml',
            stock_list_path=self.stock_list_file
        )
        
        # 测试获取所有股票
        result_all = predictor.get_available_stocks()
        self.assertIn('stocks', result_all)
        self.assertIn('sectors', result_all)
        self.assertEqual(len(result_all['stocks']), 5)
        
        # 测试按板块过滤
        result_tech = predictor.get_available_stocks(sector='tech')
        self.assertIn('stocks', result_tech)
        self.assertEqual(len(result_tech['stocks']), 3)
        self.assertIn('AAPL', result_tech['stocks'])
        
        print("✓ 获取可用股票列表成功")
        print(f"  - 总股票数: {len(result_all['stocks'])}")
        print(f"  - 板块数: {len(result_all['sectors'])}")
        print(f"  - tech板块股票数: {len(result_tech['stocks'])}")
    
    def test_7_data_preprocessing_integration(self):
        """测试数据预处理集成"""
        predictor = StockPredictor(
            config_path='config.yml',
            stock_list_path=self.stock_list_file,
            enable_preprocessing=True
        )
        
        # 生成模拟数据
        mock_data = predictor._generate_mock_data(n_days=20)
        self.assertEqual(mock_data.shape, (20, 5))
        
        # 使用预处理器
        if predictor.preprocessor:
            # fit_transform 结合 fit 和 transform
            predictor.preprocessor.fit(mock_data)
            processed = predictor.preprocessor.transform(mock_data)
            self.assertEqual(processed.shape[0], 20)
            
            # 创建序列
            sequences, targets = predictor.preprocessor.create_sequences(
                processed, seq_length=5, pred_horizon=1, include_target=True
            )
            self.assertGreater(len(sequences), 0)
            self.assertEqual(sequences.shape[1], 5)  # seq_length
            
            print("✓ 数据预处理集成成功")
            print(f"  - 原始数据形状: {mock_data.shape}")
            print(f"  - 处理后数据形状: {processed.shape}")
            print(f"  - 序列数量: {len(sequences)}")
        else:
            print("⚠ 预处理器未启用")


def run_tests():
    """运行测试套件"""
    print("\n" + "="*70)
    print("测试 Predictor 集成 StockMapper 和 DataPreprocessor")
    print("="*70 + "\n")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPredictorIntegration)
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
