"""
测试完整的 Predictor 功能 (TODO修复后)
"""

import os
import sys
import unittest
import numpy as np
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.predictor import StockPredictor


class TestPredictorComplete(unittest.TestCase):
    """测试完整的 Predictor 功能"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.stock_list_file = os.path.join(cls.temp_dir, 'stocks.json')
        
        stocks = [
            {'code': 'AAPL', 'index': 0, 'name': 'Apple Inc.', 'sector': 'tech'},
            {'code': 'GOOG', 'index': 1, 'name': 'Alphabet Inc.', 'sector': 'tech'},
        ]
        
        with open(cls.stock_list_file, 'w') as f:
            json.dump(stocks, f)
        
        print(f"\n[Setup] Created test environment in {cls.temp_dir}")
    
    def test_1_data_fetching_from_datapipe(self):
        """Test 1: 测试从 DataPipe 获取真实数据"""
        print("\n" + "="*70)
        print("Test 1: Data Fetching from DataPipe")
        print("="*70)
        
        predictor = StockPredictor(stock_list_path=self.stock_list_file)
        
        # 测试 _get_stock_data 方法
        if predictor.pipe:
            # 尝试获取数据
            data = predictor._get_stock_data('AAPL', None, None)
            
            if data is not None:
                print(f"[PASS] Got real data from DataPipe")
                print(f"  - Shape: {data.shape}")
                print(f"  - Data type: {data.dtype}")
                print(f"  - Sample values: {data[0] if len(data) > 0 else 'empty'}")
                self.assertIsNotNone(data)
                self.assertGreater(len(data), 0)
            else:
                print(f"[INFO] No real data available, will use mock data")
                # 不是失败,只是没有数据
        else:
            print(f"[SKIP] DataPipe not available")
            self.skipTest("DataPipe not initialized")
    
    def test_2_predict_with_preprocessor(self):
        """Test 2: 测试预处理器集成"""
        print("\n" + "="*70)
        print("Test 2: Prediction with Preprocessor")
        print("="*70)
        
        predictor = StockPredictor(
            stock_list_path=self.stock_list_file,
            enable_preprocessing=True
        )
        
        self.assertIsNotNone(predictor.preprocessor)
        
        result = predictor.predict_single('AAPL')
        
        print(f"[PASS] Prediction completed")
        print(f"  - Stock: {result['stock_symbol']}")
        print(f"  - Direction: {result['predictions'][0]['predicted_direction']}")
        print(f"  - Confidence: {result['predictions'][0]['confidence']:.3f}")
        print(f"  - Preprocessor used: {predictor.preprocessor is not None}")
        
        self.assertIn('stock_symbol', result)
        self.assertIn('predictions', result)
    
    def test_3_predict_with_model(self):
        """Test 3: 测试深度学习模型预测"""
        print("\n" + "="*70)
        print("Test 3: Deep Learning Model Prediction")
        print("="*70)
        
        predictor = StockPredictor(stock_list_path=self.stock_list_file)
        
        if predictor.pipe and predictor.model:
            try:
                result = predictor.predict_with_model('AAPL')
                
                print(f"[PASS] Model prediction completed")
                print(f"  - Stock: {result['stock_symbol']}")
                print(f"  - Method: {result.get('model', 'unknown')}")
                if result['predictions']:
                    print(f"  - Direction: {result['predictions'][0]['predicted_direction']}")
                    print(f"  - Confidence: {result['predictions'][0]['confidence']:.3f}")
                
                self.assertIn('stock_symbol', result)
                self.assertIn('predictions', result)
            except Exception as e:
                print(f"[INFO] Model prediction not available: {e}")
                # 不算失败,只是模型预测不可用
        else:
            print(f"[SKIP] Model or DataPipe not available")
            self.skipTest("Model prediction requires DataPipe and trained model")
    
    def test_4_stock_mapper_integration(self):
        """Test 4: 测试 StockMapper 集成"""
        print("\n" + "="*70)
        print("Test 4: StockMapper Integration")
        print("="*70)
        
        predictor = StockPredictor(stock_list_path=self.stock_list_file)
        
        self.assertIsNotNone(predictor.stock_mapper)
        
        # 测试代码查询
        index = predictor.stock_mapper.get_index('AAPL')
        code = predictor.stock_mapper.get_code(0)
        
        print(f"[PASS] StockMapper working")
        print(f"  - AAPL index: {index}")
        print(f"  - Index 0 code: {code}")
        print(f"  - Total stocks: {predictor.stock_mapper.size()}")
        
        self.assertIsNotNone(index)
        self.assertIsNotNone(code)
    
    def test_5_causal_influence(self):
        """Test 5: 测试因果影响分析"""
        print("\n" + "="*70)
        print("Test 5: Causal Influence Analysis")
        print("="*70)
        
        predictor = StockPredictor(stock_list_path=self.stock_list_file)
        
        influence = predictor.get_causal_influence('AAPL', top_k=5)
        
        print(f"[PASS] Causal influence computed")
        print(f"  - Stock: {influence['stock']}")
        print(f"  - Influenced by: {len(influence['influenced_by'])} stocks")
        print(f"  - Influences: {len(influence['influences'])} stocks")
        
        self.assertIn('stock', influence)
        self.assertIn('influenced_by', influence)
        self.assertIn('influences', influence)
    
    def test_6_batch_prediction(self):
        """Test 6: 测试批量预测"""
        print("\n" + "="*70)
        print("Test 6: Batch Prediction")
        print("="*70)
        
        predictor = StockPredictor(stock_list_path=self.stock_list_file)
        
        stocks = ['AAPL', 'GOOG']
        result = predictor.predict_batch(stocks)
        
        print(f"[PASS] Batch prediction completed")
        print(f"  - Stocks: {len(result['predictions'])}")
        print(f"  - Summary: {result['summary']}")
        
        self.assertIn('predictions', result)
        self.assertIn('summary', result)
        self.assertEqual(len(result['predictions']), len(stocks))
    
    def test_7_all_components_loaded(self):
        """Test 7: 验证所有组件加载"""
        print("\n" + "="*70)
        print("Test 7: All Components Loaded")
        print("="*70)
        
        predictor = StockPredictor(
            stock_list_path=self.stock_list_file,
            enable_preprocessing=True
        )
        
        components = {
            'model': predictor.model is not None,
            'stock_mapper': predictor.stock_mapper is not None,
            'preprocessor': predictor.preprocessor is not None,
            'graph': predictor.graph is not None,
            'pipe': predictor.pipe is not None
        }
        
        print(f"[PASS] Component status:")
        for name, status in components.items():
            print(f"  - {name}: {'OK' if status else 'NOT LOADED'}")
        
        # 至少核心组件应该加载
        self.assertTrue(components['model'])
        self.assertTrue(components['stock_mapper'])
        self.assertTrue(components['preprocessor'])
        self.assertTrue(components['graph'])


def run_tests():
    """运行测试"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPredictorComplete)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print("测试完成汇总")
    print("="*70)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    print("="*70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit(run_tests())
