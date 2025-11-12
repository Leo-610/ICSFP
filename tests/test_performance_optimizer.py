#!/usr/bin/env python3
"""
性能优化器测试
测试内存缓存、GPU加速、批处理等功能
"""

import os
import sys
import time
import unittest
import numpy as np
import tempfile
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from performance_optimizer import (
    MemoryCache,
    GPUAccelerator,
    BatchProcessor,
    PerformanceMonitor,
    PerformanceOptimizer,
    profile_function,
    create_optimizer
)


class TestMemoryCache(unittest.TestCase):
    """测试内存缓存"""
    
    def setUp(self):
        """测试前准备"""
        self.cache = MemoryCache(max_size_mb=10)  # 10MB缓存
    
    def test_put_and_get(self):
        """测试存取功能"""
        print("\n[Test] Memory Cache - Put and Get")
        
        # 存入数据
        data = np.random.randn(100, 100)
        self.cache.put('test_key', data)
        
        # 读取数据
        retrieved = self.cache.get('test_key')
        
        self.assertIsNotNone(retrieved)
        self.assertTrue(np.array_equal(data, retrieved))
        print("✓ Put and get work correctly")
    
    def test_lru_eviction(self):
        """测试LRU驱逐策略"""
        print("\n[Test] Memory Cache - LRU Eviction")
        
        # 存入多个大数组（超过缓存限制）
        arrays = []
        for i in range(5):
            arr = np.random.randn(500, 500)  # 每个约2MB
            arrays.append(arr)
            self.cache.put(f'key_{i}', arr)
        
        # 最早的键应该被驱逐
        first_key_exists = self.cache.get('key_0')
        last_key_exists = self.cache.get('key_4')
        
        print(f"  First key exists: {first_key_exists is not None}")
        print(f"  Last key exists: {last_key_exists is not None}")
        print("✓ LRU eviction works")
    
    def test_cache_stats(self):
        """测试缓存统计"""
        print("\n[Test] Memory Cache - Statistics")
        
        # 执行一些操作
        self.cache.put('key1', np.random.randn(10, 10))
        self.cache.get('key1')  # hit
        self.cache.get('key2')  # miss
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
        self.assertGreater(stats['hit_rate'], 0)
        
        print(f"✓ Stats: hits={stats['hits']}, misses={stats['misses']}, "
              f"hit_rate={stats['hit_rate']:.2%}")


class TestGPUAccelerator(unittest.TestCase):
    """测试GPU加速器"""
    
    def setUp(self):
        """测试前准备"""
        self.accelerator = GPUAccelerator()
    
    def test_tensor_conversion(self):
        """测试tensor转换"""
        print("\n[Test] GPU Accelerator - Tensor Conversion")
        
        # numpy -> tensor
        data_np = np.random.randn(10, 10).astype(np.float32)
        tensor = self.accelerator.to_tensor(data_np)
        
        # tensor -> numpy
        data_back = self.accelerator.to_numpy(tensor)
        
        self.assertTrue(np.allclose(data_np, data_back))
        print(f"✓ Conversion works correctly (device={self.accelerator.device})")
    
    def test_batch_correlation(self):
        """测试批量相关性计算"""
        print("\n[Test] GPU Accelerator - Batch Correlation")
        
        data = np.random.randn(1000, 50).astype(np.float32)
        
        start = time.time()
        corr_matrix = self.accelerator.batch_correlation(data)
        elapsed = time.time() - start
        
        self.assertEqual(corr_matrix.shape, (50, 50))
        self.assertTrue(np.allclose(corr_matrix, corr_matrix.T))  # 对称性
        
        print(f"✓ Correlation computed in {elapsed:.3f}s")
        print(f"  Shape: {corr_matrix.shape}")


class TestBatchProcessor(unittest.TestCase):
    """测试批处理器"""
    
    def setUp(self):
        """测试前准备"""
        self.processor = BatchProcessor(batch_size=10, num_workers=2)
    
    def test_process_batches(self):
        """测试批量处理"""
        print("\n[Test] Batch Processor - Process Batches")
        
        data = np.arange(100).reshape(100, 1)
        
        def process_fn(batch):
            return batch.sum()
        
        results = self.processor.process_batches(data, process_fn)
        
        total_sum = sum(results)
        expected_sum = data.sum()
        
        self.assertEqual(total_sum, expected_sum)
        print(f"✓ Batch processing works: {len(results)} batches, sum={total_sum}")
    
    def test_parallel_map(self):
        """测试并行映射"""
        print("\n[Test] Batch Processor - Parallel Map")
        
        items = list(range(100))
        
        def square(x):
            return x ** 2
        
        start = time.time()
        results = self.processor.parallel_map(items, square, use_threads=True)
        elapsed = time.time() - start
        
        expected = [x ** 2 for x in items]
        
        self.assertEqual(results, expected)
        print(f"✓ Parallel map completed in {elapsed:.3f}s")


class TestPerformanceMonitor(unittest.TestCase):
    """测试性能监控器"""
    
    def test_timing(self):
        """测试计时功能"""
        print("\n[Test] Performance Monitor - Timing")
        
        monitor = PerformanceMonitor()
        
        monitor.start()
        time.sleep(0.1)  # 模拟计算
        elapsed = monitor.stop()
        
        self.assertGreater(elapsed, 0.09)
        self.assertLess(elapsed, 0.15)
        
        print(f"✓ Timing works: {elapsed:.3f}s")
    
    def test_memory_recording(self):
        """测试内存记录"""
        print("\n[Test] Performance Monitor - Memory Recording")
        
        monitor = PerformanceMonitor()
        
        mem_usage = monitor.record_memory()
        
        self.assertGreater(mem_usage, 0)
        print(f"✓ Memory recorded: {mem_usage:.2f}MB")
    
    def test_summary(self):
        """测试统计摘要"""
        print("\n[Test] Performance Monitor - Summary")
        
        monitor = PerformanceMonitor()
        
        # 记录一些数据
        for _ in range(5):
            monitor.start()
            time.sleep(0.01)
            monitor.stop()
            monitor.record_memory()
        
        summary = monitor.get_summary()
        
        self.assertIn('execution_times', summary)
        self.assertEqual(summary['execution_times']['count'], 5)
        
        print(f"✓ Summary generated: {summary['execution_times']['count']} records")


class TestPerformanceOptimizer(unittest.TestCase):
    """测试性能优化器（集成测试）"""
    
    def setUp(self):
        """测试前准备"""
        self.optimizer = create_optimizer(
            cache_size_mb=50,
            use_gpu=False,  # 避免GPU依赖
            batch_size=16,
            num_workers=2
        )
        
        # 生成测试数据
        np.random.seed(42)
        self.test_data = np.cumsum(np.random.randn(500, 20), axis=0)
    
    def test_cached_compute(self):
        """测试带缓存的计算"""
        print("\n[Test] Performance Optimizer - Cached Compute")
        
        def expensive_compute(data):
            time.sleep(0.1)  # 模拟耗时计算
            return np.mean(data)
        
        # 第一次计算（缓存未命中）
        start = time.time()
        result1 = self.optimizer.cached_compute(
            'test_compute', expensive_compute, self.test_data
        )
        time1 = time.time() - start
        
        # 第二次计算（缓存命中）
        start = time.time()
        result2 = self.optimizer.cached_compute(
            'test_compute', expensive_compute, self.test_data
        )
        time2 = time.time() - start
        
        self.assertEqual(result1, result2)
        self.assertGreater(time1, time2)  # 缓存应该更快
        
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"✓ Cache speedup: {speedup:.1f}x ({time1:.3f}s -> {time2:.3f}s)")
    
    def test_optimize_causal_discovery(self):
        """测试优化的因果发现"""
        print("\n[Test] Performance Optimizer - Causal Discovery")
        
        # 测试相关性方法
        start = time.time()
        graph1 = self.optimizer.optimize_causal_discovery(
            self.test_data,
            method='correlation',
            threshold=0.3
        )
        time1 = time.time() - start
        
        self.assertEqual(graph1.shape, (20, 20))
        self.assertEqual(np.diag(graph1).sum(), 0)  # 对角线应为0
        
        print(f"✓ Correlation method: {time1:.3f}s")
        print(f"  Edges: {np.count_nonzero(graph1)}")
        
        # 测试滞后相关性方法
        start = time.time()
        graph2 = self.optimizer.optimize_causal_discovery(
            self.test_data,
            method='lagged_correlation',
            max_lag=3,
            threshold=0.3
        )
        time2 = time.time() - start
        
        self.assertEqual(graph2.shape, (20, 20))
        
        print(f"✓ Lagged correlation method: {time2:.3f}s")
        print(f"  Edges: {np.count_nonzero(graph2)}")
    
    def test_statistics(self):
        """测试统计信息"""
        print("\n[Test] Performance Optimizer - Statistics")
        
        # 执行一些操作以生成统计
        self.optimizer.optimize_causal_discovery(
            self.test_data, method='correlation'
        )
        self.optimizer.optimize_causal_discovery(
            self.test_data, method='correlation'  # 缓存命中
        )
        
        stats = self.optimizer.get_statistics()
        
        self.assertIn('cache', stats)
        self.assertIn('performance', stats)
        self.assertGreater(stats['cache']['hit_rate'], 0)
        
        print(f"✓ Cache hit rate: {stats['cache']['hit_rate']:.2%}")
        print(f"  Cached items: {stats['cache']['num_items']}")
        print(f"  Cache size: {stats['cache']['current_size_mb']:.2f}MB")
    
    def test_clear_caches(self):
        """测试清空缓存"""
        print("\n[Test] Performance Optimizer - Clear Caches")
        
        # 添加一些缓存数据
        self.optimizer.optimize_causal_discovery(
            self.test_data, method='correlation'
        )
        
        stats_before = self.optimizer.get_statistics()
        items_before = stats_before['cache']['num_items']
        
        # 清空缓存
        self.optimizer.clear_all_caches()
        
        stats_after = self.optimizer.get_statistics()
        items_after = stats_after['cache']['num_items']
        
        self.assertEqual(items_after, 0)
        
        print(f"✓ Cleared {items_before} cached items")


class TestProfileDecorator(unittest.TestCase):
    """测试性能分析装饰器"""
    
    def test_profile_function(self):
        """测试函数分析装饰器"""
        print("\n[Test] Profile Decorator")
        
        @profile_function
        def test_func(n):
            data = np.random.randn(n, n)
            return np.sum(data)
        
        result = test_func(1000)
        
        self.assertIsInstance(result, (int, float, np.number))
        print("✓ Profile decorator works")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("PERFORMANCE OPTIMIZER TESTS")
    print("=" * 70)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryCache))
    suite.addTests(loader.loadTestsFromTestCase(TestGPUAccelerator))
    suite.addTests(loader.loadTestsFromTestCase(TestBatchProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceOptimizer))
    suite.addTests(loader.loadTestsFromTestCase(TestProfileDecorator))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印摘要
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
