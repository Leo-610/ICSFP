#!/usr/bin/env python3
"""
性能优化器 (Performance Optimizer)
针对因果发现、预测和数据处理的系统性能优化

优化策略:
1. GPU加速因果推断
2. 多级缓存机制(内存+磁盘)
3. 批处理优化
4. 内存使用优化
5. 异步计算
"""

import os
import time
import psutil
import logging
import numpy as np
import torch
import pickle
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable
from functools import wraps, lru_cache
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading

logger = logging.getLogger(__name__)


class MemoryCache:
    """内存缓存管理器（LRU策略）"""
    
    def __init__(self, max_size_mb: int = 512):
        """
        初始化内存缓存
        
        Args:
            max_size_mb: 最大缓存大小(MB)
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.cache_sizes = {}
        self.current_size = 0
        self.lock = threading.Lock()
        
        self.hits = 0
        self.misses = 0
        
        logger.info(f"MemoryCache initialized: max_size={max_size_mb}MB")
    
    def _compute_size(self, obj: Any) -> int:
        """计算对象大小"""
        if isinstance(obj, np.ndarray):
            return obj.nbytes
        elif isinstance(obj, torch.Tensor):
            return obj.element_size() * obj.nelement()
        else:
            # 使用pickle序列化估计大小
            return len(pickle.dumps(obj))
    
    def _evict_lru(self, required_size: int):
        """驱逐最久未使用的缓存项"""
        while self.current_size + required_size > self.max_size_bytes and self.cache:
            key, value = self.cache.popitem(last=False)
            size = self.cache_sizes.pop(key)
            self.current_size -= size
            logger.debug(f"Evicted cache key: {key}, freed {size/1024/1024:.2f}MB")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        with self.lock:
            if key in self.cache:
                self.hits += 1
                # 移动到末尾（最近使用）
                self.cache.move_to_end(key)
                return self.cache[key]
            else:
                self.misses += 1
                return None
    
    def put(self, key: str, value: Any):
        """存入缓存"""
        with self.lock:
            size = self._compute_size(value)
            
            # 如果键已存在，先删除旧值
            if key in self.cache:
                old_size = self.cache_sizes[key]
                self.current_size -= old_size
                del self.cache[key]
                del self.cache_sizes[key]
            
            # 驱逐旧项腾出空间
            self._evict_lru(size)
            
            # 添加新项
            self.cache[key] = value
            self.cache_sizes[key] = size
            self.current_size += size
            
            logger.debug(f"Cached key: {key}, size={size/1024/1024:.2f}MB, "
                        f"total={self.current_size/1024/1024:.2f}MB")
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.cache_sizes.clear()
            self.current_size = 0
            logger.info("Memory cache cleared")
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'current_size_mb': self.current_size / 1024 / 1024,
            'max_size_mb': self.max_size_bytes / 1024 / 1024,
            'num_items': len(self.cache)
        }


class GPUAccelerator:
    """GPU加速计算管理器"""
    
    def __init__(self, device: Optional[str] = None):
        """
        初始化GPU加速器
        
        Args:
            device: 计算设备 ('cuda', 'cpu' 或 None=自动检测)
        """
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        self.is_gpu = self.device.startswith('cuda')
        
        if self.is_gpu:
            self.gpu_name = torch.cuda.get_device_name(0)
            self.gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"GPU accelerator enabled: {self.gpu_name} ({self.gpu_memory:.2f}GB)")
        else:
            logger.info("Running on CPU")
    
    def to_tensor(self, data: np.ndarray, dtype=torch.float32) -> torch.Tensor:
        """将numpy数组转换为tensor并移到GPU"""
        tensor = torch.from_numpy(data).to(dtype)
        return tensor.to(self.device)
    
    def to_numpy(self, tensor: torch.Tensor) -> np.ndarray:
        """将tensor转换为numpy数组"""
        return tensor.cpu().numpy()
    
    def batch_correlation(
        self,
        data: np.ndarray,
        batch_size: int = 100
    ) -> np.ndarray:
        """
        批量计算相关性矩阵（GPU加速）
        
        Args:
            data: 时间序列数据 (T, N)
            batch_size: 批处理大小
            
        Returns:
            correlation_matrix: 相关性矩阵 (N, N)
        """
        T, N = data.shape
        
        # 标准化数据
        data_tensor = self.to_tensor(data)
        data_mean = data_tensor.mean(dim=0, keepdim=True)
        data_std = data_tensor.std(dim=0, keepdim=True) + 1e-8
        data_normalized = (data_tensor - data_mean) / data_std
        
        # 计算相关性
        correlation = torch.mm(data_normalized.t(), data_normalized) / T
        
        return self.to_numpy(correlation)
    
    def batch_lagged_correlation(
        self,
        data: np.ndarray,
        max_lag: int = 5,
        batch_size: int = 50
    ) -> np.ndarray:
        """
        批量计算滞后相关性（用于因果推断）
        
        Args:
            data: 时间序列数据 (T, N)
            max_lag: 最大滞后
            batch_size: 批处理大小
            
        Returns:
            lagged_corr: 滞后相关性矩阵 (N, N)
        """
        T, N = data.shape
        data_tensor = self.to_tensor(data)
        
        # 标准化
        data_mean = data_tensor.mean(dim=0, keepdim=True)
        data_std = data_tensor.std(dim=0, keepdim=True) + 1e-8
        data_normalized = (data_tensor - data_mean) / data_std
        
        # 初始化结果矩阵
        lagged_corr = torch.zeros((N, N), device=self.device)
        
        # 批量计算
        for batch_start in range(0, N, batch_size):
            batch_end = min(batch_start + batch_size, N)
            
            for i in range(batch_start, batch_end):
                for j in range(N):
                    if i == j:
                        continue
                    
                    max_corr = 0.0
                    for lag in range(1, min(max_lag + 1, T // 10)):
                        if T - lag > 10:
                            # 计算 data[lag:, i] 和 data[:-lag, j] 的相关性
                            x = data_normalized[lag:, i]
                            y = data_normalized[:-lag, j]
                            corr = torch.dot(x, y) / len(x)
                            max_corr = max(max_corr, abs(corr.item()))
                    
                    lagged_corr[i, j] = max_corr
        
        return self.to_numpy(lagged_corr)
    
    def clear_cache(self):
        """清理GPU缓存"""
        if self.is_gpu:
            torch.cuda.empty_cache()
            logger.debug("GPU cache cleared")


class BatchProcessor:
    """批处理优化器"""
    
    def __init__(
        self,
        batch_size: int = 32,
        num_workers: int = 4,
        use_gpu: bool = True
    ):
        """
        初始化批处理器
        
        Args:
            batch_size: 批处理大小
            num_workers: 工作进程数
            use_gpu: 是否使用GPU
        """
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.gpu_accelerator = GPUAccelerator() if use_gpu else None
        
        logger.info(f"BatchProcessor initialized: batch_size={batch_size}, "
                   f"num_workers={num_workers}, use_gpu={use_gpu}")
    
    def process_batches(
        self,
        data: np.ndarray,
        process_fn: Callable,
        **kwargs
    ) -> List[Any]:
        """
        批量处理数据
        
        Args:
            data: 输入数据
            process_fn: 处理函数
            **kwargs: 处理函数参数
            
        Returns:
            results: 处理结果列表
        """
        n_samples = len(data)
        results = []
        
        for i in range(0, n_samples, self.batch_size):
            batch_end = min(i + self.batch_size, n_samples)
            batch_data = data[i:batch_end]
            
            batch_result = process_fn(batch_data, **kwargs)
            results.append(batch_result)
        
        return results
    
    def parallel_map(
        self,
        items: List[Any],
        map_fn: Callable,
        use_threads: bool = True
    ) -> List[Any]:
        """
        并行映射处理
        
        Args:
            items: 待处理项目列表
            map_fn: 映射函数
            use_threads: 使用线程池(True)或进程池(False)
            
        Returns:
            results: 处理结果列表
        """
        ExecutorClass = ThreadPoolExecutor if use_threads else ProcessPoolExecutor
        
        with ExecutorClass(max_workers=self.num_workers) as executor:
            results = list(executor.map(map_fn, items))
        
        return results


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        """初始化性能监控器"""
        self.metrics = {
            'execution_times': [],
            'memory_usage': [],
            'gpu_usage': [],
            'cache_hits': [],
            'cache_misses': []
        }
        self.start_time = None
    
    def start(self):
        """开始监控"""
        self.start_time = time.time()
    
    def stop(self) -> float:
        """停止监控并返回耗时"""
        if self.start_time is None:
            return 0.0
        
        elapsed = time.time() - self.start_time
        self.metrics['execution_times'].append(elapsed)
        self.start_time = None
        
        return elapsed
    
    def record_memory(self):
        """记录内存使用"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.metrics['memory_usage'].append(memory_mb)
        
        return memory_mb
    
    def record_gpu(self):
        """记录GPU使用"""
        if torch.cuda.is_available():
            gpu_mb = torch.cuda.memory_allocated() / 1024 / 1024
            self.metrics['gpu_usage'].append(gpu_mb)
            return gpu_mb
        return 0.0
    
    def get_summary(self) -> Dict:
        """获取性能摘要"""
        summary = {}
        
        for key, values in self.metrics.items():
            if len(values) > 0:
                summary[key] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'count': len(values)
                }
            else:
                summary[key] = {'count': 0}
        
        return summary


class PerformanceOptimizer:
    """
    系统性能优化器
    集成所有优化组件
    """
    
    def __init__(
        self,
        cache_size_mb: int = 512,
        use_gpu: bool = True,
        batch_size: int = 32,
        num_workers: int = 4
    ):
        """
        初始化性能优化器
        
        Args:
            cache_size_mb: 内存缓存大小(MB)
            use_gpu: 是否使用GPU
            batch_size: 批处理大小
            num_workers: 工作进程数
        """
        self.memory_cache = MemoryCache(max_size_mb=cache_size_mb)
        self.gpu_accelerator = GPUAccelerator() if use_gpu else None
        self.batch_processor = BatchProcessor(
            batch_size=batch_size,
            num_workers=num_workers,
            use_gpu=use_gpu
        )
        self.monitor = PerformanceMonitor()
        
        logger.info(f"PerformanceOptimizer initialized: cache={cache_size_mb}MB, "
                   f"gpu={use_gpu}, batch={batch_size}, workers={num_workers}")
    
    def cached_compute(
        self,
        cache_key: str,
        compute_fn: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        带缓存的计算
        
        Args:
            cache_key: 缓存键
            compute_fn: 计算函数
            *args, **kwargs: 函数参数
            
        Returns:
            result: 计算结果（从缓存或新计算）
        """
        # 尝试从缓存获取
        result = self.memory_cache.get(cache_key)
        
        if result is not None:
            logger.debug(f"Cache hit: {cache_key}")
            return result
        
        # 缓存未命中，执行计算
        logger.debug(f"Cache miss: {cache_key}, computing...")
        
        self.monitor.start()
        result = compute_fn(*args, **kwargs)
        elapsed = self.monitor.stop()
        
        # 存入缓存
        self.memory_cache.put(cache_key, result)
        
        logger.debug(f"Computed and cached {cache_key} in {elapsed:.3f}s")
        
        return result
    
    def optimize_causal_discovery(
        self,
        data: np.ndarray,
        method: str = 'correlation',
        max_lag: int = 5,
        threshold: float = 0.3
    ) -> np.ndarray:
        """
        优化的因果发现计算
        
        Args:
            data: 时间序列数据 (T, N)
            method: 方法 ('correlation', 'lagged_correlation')
            max_lag: 最大滞后
            threshold: 阈值
            
        Returns:
            causal_graph: 因果图 (N, N)
        """
        # 生成缓存键
        data_hash = hashlib.md5(data.tobytes()).hexdigest()[:16]
        cache_key = f"causal_{method}_{data_hash}_{max_lag}_{threshold}"
        
        def compute():
            if method == 'correlation':
                if self.gpu_accelerator:
                    corr = self.gpu_accelerator.batch_correlation(data)
                else:
                    corr = np.corrcoef(data.T)
                
                # 应用阈值
                causal_graph = np.abs(corr)
                causal_graph[causal_graph < threshold] = 0
                np.fill_diagonal(causal_graph, 0)
                
                return causal_graph
                
            elif method == 'lagged_correlation':
                if self.gpu_accelerator:
                    lagged_corr = self.gpu_accelerator.batch_lagged_correlation(
                        data, max_lag=max_lag
                    )
                else:
                    # CPU版本
                    N = data.shape[1]
                    lagged_corr = np.zeros((N, N))
                    
                    for i in range(N):
                        for j in range(N):
                            if i == j:
                                continue
                            
                            max_corr = 0.0
                            for lag in range(1, min(max_lag + 1, len(data) // 10)):
                                if len(data) - lag > 10:
                                    corr = np.corrcoef(
                                        data[lag:, i],
                                        data[:-lag, j]
                                    )[0, 1]
                                    max_corr = max(max_corr, abs(corr))
                            
                            lagged_corr[i, j] = max_corr
                
                # 应用阈值
                causal_graph = lagged_corr
                causal_graph[causal_graph < threshold] = 0
                
                return causal_graph
            
            else:
                raise ValueError(f"Unknown method: {method}")
        
        return self.cached_compute(cache_key, compute)
    
    def get_statistics(self) -> Dict:
        """获取优化器统计信息"""
        stats = {
            'cache': self.memory_cache.get_stats(),
            'performance': self.monitor.get_summary(),
            'gpu_available': torch.cuda.is_available()
        }
        
        if torch.cuda.is_available():
            stats['gpu_info'] = {
                'name': torch.cuda.get_device_name(0),
                'memory_total_gb': torch.cuda.get_device_properties(0).total_memory / 1024**3,
                'memory_allocated_mb': torch.cuda.memory_allocated() / 1024**2,
                'memory_reserved_mb': torch.cuda.memory_reserved() / 1024**2
            }
        
        return stats
    
    def clear_all_caches(self):
        """清空所有缓存"""
        self.memory_cache.clear()
        if self.gpu_accelerator:
            self.gpu_accelerator.clear_cache()
        logger.info("All caches cleared")


def profile_function(func: Callable) -> Callable:
    """
    函数性能分析装饰器
    
    用法:
        @profile_function
        def my_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # 记录内存
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 记录结束
        elapsed = time.time() - start_time
        mem_after = process.memory_info().rss / 1024 / 1024
        mem_delta = mem_after - mem_before
        
        logger.info(f"[PROFILE] {func.__name__}: "
                   f"time={elapsed:.3f}s, memory_delta={mem_delta:+.2f}MB")
        
        return result
    
    return wrapper


# 便捷函数
def create_optimizer(
    cache_size_mb: int = 512,
    use_gpu: bool = True,
    batch_size: int = 32,
    num_workers: int = 4
) -> PerformanceOptimizer:
    """
    创建性能优化器实例
    
    Args:
        cache_size_mb: 内存缓存大小
        use_gpu: 是否使用GPU
        batch_size: 批处理大小
        num_workers: 工作进程数
        
    Returns:
        optimizer: 性能优化器实例
    """
    return PerformanceOptimizer(
        cache_size_mb=cache_size_mb,
        use_gpu=use_gpu,
        batch_size=batch_size,
        num_workers=num_workers
    )


if __name__ == '__main__':
    # 测试代码
    print("=" * 70)
    print("PERFORMANCE OPTIMIZER - TEST")
    print("=" * 70)
    
    # 创建优化器
    optimizer = create_optimizer(cache_size_mb=256, use_gpu=True)
    
    # 生成测试数据
    n_stocks = 50
    n_timepoints = 1000
    data = np.cumsum(np.random.randn(n_timepoints, n_stocks), axis=0)
    
    print(f"\nTest data: {n_timepoints} timepoints, {n_stocks} stocks")
    
    # 测试1: 相关性计算（缓存未命中）
    print("\n" + "=" * 70)
    print("TEST 1: Correlation Computation (Cache Miss)")
    print("=" * 70)
    start = time.time()
    graph1 = optimizer.optimize_causal_discovery(
        data, method='correlation', threshold=0.3
    )
    time1 = time.time() - start
    print(f"✓ Computed in {time1:.3f}s")
    print(f"✓ Graph shape: {graph1.shape}")
    print(f"✓ Non-zero edges: {np.count_nonzero(graph1)}")
    
    # 测试2: 相同计算（缓存命中）
    print("\n" + "=" * 70)
    print("TEST 2: Same Computation (Cache Hit)")
    print("=" * 70)
    start = time.time()
    graph2 = optimizer.optimize_causal_discovery(
        data, method='correlation', threshold=0.3
    )
    time2 = time.time() - start
    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"✓ Retrieved in {time2:.3f}s")
    print(f"✓ Speedup: {speedup:.1f}x")
    print(f"✓ Graphs identical: {np.array_equal(graph1, graph2)}")
    
    # 测试3: 滞后相关性（GPU加速）
    print("\n" + "=" * 70)
    print("TEST 3: Lagged Correlation (GPU Accelerated)")
    print("=" * 70)
    start = time.time()
    graph3 = optimizer.optimize_causal_discovery(
        data, method='lagged_correlation', max_lag=5, threshold=0.3
    )
    time3 = time.time() - start
    print(f"✓ Computed in {time3:.3f}s")
    print(f"✓ Graph shape: {graph3.shape}")
    print(f"✓ Non-zero edges: {np.count_nonzero(graph3)}")
    
    # 测试4: 统计信息
    print("\n" + "=" * 70)
    print("TEST 4: Optimizer Statistics")
    print("=" * 70)
    stats = optimizer.get_statistics()
    print(f"✓ Cache hit rate: {stats['cache']['hit_rate']:.2%}")
    print(f"✓ Cache size: {stats['cache']['current_size_mb']:.2f}MB")
    print(f"✓ Cached items: {stats['cache']['num_items']}")
    
    if stats['gpu_available']:
        print(f"✓ GPU: {stats['gpu_info']['name']}")
        print(f"✓ GPU memory: {stats['gpu_info']['memory_allocated_mb']:.2f}MB")
    
    # 清理
    optimizer.clear_all_caches()
    print("\n✓ Caches cleared")
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED!")
    print("=" * 70)
