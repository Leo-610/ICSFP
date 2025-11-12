"""
Performance Optimization Module for ICSFP
使用 ic_sfp_gpu 环境进行 GPU 加速和性能优化

Features:
1. GPU-accelerated causal inference
2. Smart caching with compression
3. Batch processing optimization
4. Memory management
5. Performance monitoring
"""

import torch
import numpy as np
import logging
import time
import psutil
import pickle
import gzip
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from functools import lru_cache
from joblib import Memory
import hashlib

logger = logging.getLogger(__name__)


class GPUAccelerator:
    """GPU 加速器 - 使用 PyTorch GPU 加速因果推断计算"""
    
    def __init__(self, device: Optional[str] = None):
        """
        初始化 GPU 加速器
        
        Args:
            device: 设备类型 ('cuda', 'cpu', None=自动检测)
        """
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        if self.device.type == 'cuda':
            logger.info(f"✅ GPU 加速已启用: {torch.cuda.get_device_name(0)}")
            logger.info(f"   GPU 内存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        else:
            logger.warning("⚠️ GPU 不可用，使用 CPU 模式")
    
    def to_gpu(self, data: np.ndarray) -> torch.Tensor:
        """将 NumPy 数组转移到 GPU"""
        return torch.from_numpy(data).float().to(self.device)
    
    def to_cpu(self, tensor: torch.Tensor) -> np.ndarray:
        """将 GPU 张量转回 CPU NumPy 数组"""
        return tensor.cpu().numpy()
    
    def compute_correlation_matrix(self, data: np.ndarray) -> np.ndarray:
        """
        GPU 加速计算相关系数矩阵
        
        Args:
            data: shape (n_samples, n_features)
        
        Returns:
            相关系数矩阵 shape (n_features, n_features)
        """
        try:
            # 转移到 GPU
            data_gpu = self.to_gpu(data)
            
            # 标准化
            mean = data_gpu.mean(dim=0, keepdim=True)
            std = data_gpu.std(dim=0, keepdim=True) + 1e-8
            data_norm = (data_gpu - mean) / std
            
            # 计算相关系数矩阵
            n_samples = data_norm.shape[0]
            corr_matrix = torch.mm(data_norm.t(), data_norm) / (n_samples - 1)
            
            # 转回 CPU
            return self.to_cpu(corr_matrix)
            
        except RuntimeError as e:
            if "out of memory" in str(e):
                logger.warning("GPU 内存不足，回退到 CPU 计算")
                torch.cuda.empty_cache()
                # 使用 NumPy 计算
                return np.corrcoef(data.T)
            raise
    
    def batch_matrix_multiply(self, matrices: List[np.ndarray]) -> np.ndarray:
        """
        批量矩阵乘法 (GPU 加速)
        
        Args:
            matrices: 矩阵列表
        
        Returns:
            所有矩阵的乘积
        """
        if not matrices:
            raise ValueError("矩阵列表不能为空")
        
        result = self.to_gpu(matrices[0])
        for mat in matrices[1:]:
            mat_gpu = self.to_gpu(mat)
            result = torch.mm(result, mat_gpu)
        
        return self.to_cpu(result)
    
    def parallel_granger_test(self, data: np.ndarray, max_lag: int = 5) -> np.ndarray:
        """
        并行 Granger 因果检验 (GPU 加速)
        
        Args:
            data: 时间序列数据 shape (n_samples, n_features)
            max_lag: 最大滞后阶数
        
        Returns:
            因果图矩阵 shape (n_features, n_features)
        """
        n_samples, n_features = data.shape
        causal_matrix = np.zeros((n_features, n_features))
        
        try:
            data_gpu = self.to_gpu(data)
            
            # 为每对变量计算 Granger 因果关系
            for i in range(n_features):
                for j in range(n_features):
                    if i == j:
                        continue
                    
                    # 简化的 Granger 检验: 使用相关系数作为因果强度
                    # 计算 X_j 对 X_i 的滞后相关性
                    causality_score = 0.0
                    for lag in range(1, max_lag + 1):
                        if lag >= n_samples:
                            break
                        
                        x_i_current = data_gpu[lag:, i]
                        x_j_lagged = data_gpu[:-lag, j]
                        
                        # 计算相关系数
                        x_i_mean = x_i_current.mean()
                        x_j_mean = x_j_lagged.mean()
                        x_i_std = x_i_current.std() + 1e-8
                        x_j_std = x_j_lagged.std() + 1e-8
                        
                        corr = ((x_i_current - x_i_mean) * (x_j_lagged - x_j_mean)).mean()
                        corr = corr / (x_i_std * x_j_std)
                        
                        causality_score += abs(corr.item()) / max_lag
                    
                    causal_matrix[i, j] = causality_score
            
            return causal_matrix
            
        except RuntimeError as e:
            if "out of memory" in str(e):
                logger.warning("GPU 内存不足，回退到 CPU 计算")
                torch.cuda.empty_cache()
                # 简单的相关系数方法
                return np.abs(np.corrcoef(data.T))
            raise
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取 GPU/CPU 内存使用情况"""
        memory_info = {
            'cpu_percent': psutil.virtual_memory().percent,
            'cpu_available_gb': psutil.virtual_memory().available / 1e9
        }
        
        if self.device.type == 'cuda':
            memory_info.update({
                'gpu_allocated_gb': torch.cuda.memory_allocated() / 1e9,
                'gpu_reserved_gb': torch.cuda.memory_reserved() / 1e9,
                'gpu_free_gb': (torch.cuda.get_device_properties(0).total_memory - 
                               torch.cuda.memory_allocated()) / 1e9
            })
        
        return memory_info


class SmartCache:
    """智能缓存系统 - 支持内存缓存、磁盘缓存、压缩"""
    
    def __init__(self, cache_dir: str = './cache', max_memory_mb: int = 1024):
        """
        初始化缓存系统
        
        Args:
            cache_dir: 缓存目录
            max_memory_mb: 最大内存缓存大小 (MB)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_memory_mb = max_memory_mb
        
        # 内存缓存
        self.memory_cache: Dict[str, Any] = {}
        self.cache_sizes: Dict[str, int] = {}  # 跟踪缓存大小
        self.cache_access_count: Dict[str, int] = {}  # 跟踪访问次数
        
        # 磁盘缓存 (使用 joblib Memory)
        self.disk_cache = Memory(location=str(self.cache_dir / 'joblib'), verbose=0)
        
        logger.info(f"✅ 缓存系统已初始化: {self.cache_dir}")
        logger.info(f"   最大内存缓存: {max_memory_mb} MB")
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_str = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_data_size(self, data: Any) -> int:
        """估算数据大小 (bytes)"""
        if isinstance(data, np.ndarray):
            return data.nbytes
        elif isinstance(data, torch.Tensor):
            return data.element_size() * data.nelement()
        else:
            # 使用 pickle 估算
            return len(pickle.dumps(data))
    
    def _evict_if_needed(self, new_size: int):
        """如果内存不足，驱逐最少使用的缓存"""
        current_size = sum(self.cache_sizes.values())
        max_size = self.max_memory_mb * 1024 * 1024
        
        if current_size + new_size > max_size:
            # 按访问次数排序，驱逐最少使用的
            sorted_keys = sorted(self.cache_access_count.items(), key=lambda x: x[1])
            
            for key, _ in sorted_keys:
                if current_size + new_size <= max_size:
                    break
                
                current_size -= self.cache_sizes[key]
                del self.memory_cache[key]
                del self.cache_sizes[key]
                del self.cache_access_count[key]
                logger.debug(f"驱逐缓存: {key}")
    
    def get(self, key: str, default=None) -> Any:
        """从缓存获取数据"""
        # 先查内存缓存
        if key in self.memory_cache:
            self.cache_access_count[key] = self.cache_access_count.get(key, 0) + 1
            logger.debug(f"内存缓存命中: {key}")
            return self.memory_cache[key]
        
        # 再查磁盘缓存
        disk_file = self.cache_dir / f"{key}.pkl.gz"
        if disk_file.exists():
            logger.debug(f"磁盘缓存命中: {key}")
            with gzip.open(disk_file, 'rb') as f:
                data = pickle.load(f)
            
            # 加载到内存缓存
            data_size = self._get_data_size(data)
            self._evict_if_needed(data_size)
            self.memory_cache[key] = data
            self.cache_sizes[key] = data_size
            self.cache_access_count[key] = 1
            
            return data
        
        logger.debug(f"缓存未命中: {key}")
        return default
    
    def set(self, key: str, value: Any, compress: bool = True):
        """设置缓存数据"""
        data_size = self._get_data_size(value)
        
        # 内存缓存
        self._evict_if_needed(data_size)
        self.memory_cache[key] = value
        self.cache_sizes[key] = data_size
        self.cache_access_count[key] = 1
        
        # 磁盘缓存 (压缩)
        if compress:
            disk_file = self.cache_dir / f"{key}.pkl.gz"
            with gzip.open(disk_file, 'wb') as f:
                pickle.dump(value, f)
            logger.debug(f"缓存已保存 (压缩): {key}, 大小: {data_size / 1024:.2f} KB")
        else:
            disk_file = self.cache_dir / f"{key}.pkl"
            with open(disk_file, 'wb') as f:
                pickle.dump(value, f)
            logger.debug(f"缓存已保存: {key}, 大小: {data_size / 1024:.2f} KB")
    
    def clear(self):
        """清空所有缓存"""
        self.memory_cache.clear()
        self.cache_sizes.clear()
        self.cache_access_count.clear()
        
        # 清空磁盘缓存
        for cache_file in self.cache_dir.glob("*.pkl*"):
            cache_file.unlink()
        
        logger.info("✅ 缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_memory = sum(self.cache_sizes.values())
        disk_files = list(self.cache_dir.glob("*.pkl*"))
        total_disk = sum(f.stat().st_size for f in disk_files)
        
        return {
            'memory_items': len(self.memory_cache),
            'memory_size_mb': total_memory / 1024 / 1024,
            'disk_items': len(disk_files),
            'disk_size_mb': total_disk / 1024 / 1024,
            'hit_rate': sum(self.cache_access_count.values()) / max(len(self.memory_cache), 1)
        }


class BatchProcessor:
    """批处理优化器 - 智能批量处理数据"""
    
    def __init__(self, batch_size: int = 32, num_workers: int = 4):
        """
        初始化批处理器
        
        Args:
            batch_size: 批大小
            num_workers: 并行工作进程数
        """
        self.batch_size = batch_size
        self.num_workers = num_workers
        logger.info(f"✅ 批处理器已初始化: batch_size={batch_size}, workers={num_workers}")
    
    def process_in_batches(self, data: List[Any], 
                          process_fn: callable,
                          desc: str = "Processing") -> List[Any]:
        """
        批量处理数据
        
        Args:
            data: 数据列表
            process_fn: 处理函数
            desc: 进度描述
        
        Returns:
            处理结果列表
        """
        results = []
        total_batches = (len(data) + self.batch_size - 1) // self.batch_size
        
        logger.info(f"开始批处理: {len(data)} 项, {total_batches} 批")
        
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            start_time = time.time()
            batch_results = [process_fn(item) for item in batch]
            elapsed = time.time() - start_time
            
            results.extend(batch_results)
            
            logger.debug(f"批次 {batch_num}/{total_batches} 完成, "
                        f"耗时: {elapsed:.2f}s, "
                        f"速度: {len(batch)/elapsed:.2f} items/s")
        
        logger.info(f"✅ 批处理完成: {len(results)} 项")
        return results


class PerformanceMonitor:
    """性能监控器 - 跟踪系统性能指标"""
    
    def __init__(self):
        """初始化性能监控器"""
        self.metrics: Dict[str, List[float]] = {
            'cpu_percent': [],
            'memory_percent': [],
            'execution_time': [],
        }
        self.start_time = None
        
        # GPU 监控
        if torch.cuda.is_available():
            self.metrics.update({
                'gpu_memory_allocated': [],
                'gpu_memory_reserved': []
            })
        
        logger.info("✅ 性能监控器已初始化")
    
    def start(self):
        """开始监控"""
        self.start_time = time.time()
    
    def record(self):
        """记录当前性能指标"""
        self.metrics['cpu_percent'].append(psutil.cpu_percent())
        self.metrics['memory_percent'].append(psutil.virtual_memory().percent)
        
        if torch.cuda.is_available():
            self.metrics['gpu_memory_allocated'].append(
                torch.cuda.memory_allocated() / 1e9
            )
            self.metrics['gpu_memory_reserved'].append(
                torch.cuda.memory_reserved() / 1e9
            )
        
        if self.start_time:
            self.metrics['execution_time'].append(time.time() - self.start_time)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {}
        
        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    'mean': np.mean(values),
                    'max': np.max(values),
                    'min': np.min(values),
                    'std': np.std(values)
                }
        
        return summary
    
    def print_summary(self):
        """打印性能摘要"""
        summary = self.get_summary()
        
        logger.info("=" * 60)
        logger.info("性能监控摘要")
        logger.info("=" * 60)
        
        for metric_name, stats in summary.items():
            logger.info(f"{metric_name}:")
            logger.info(f"  平均: {stats['mean']:.2f}")
            logger.info(f"  最大: {stats['max']:.2f}")
            logger.info(f"  最小: {stats['min']:.2f}")
            logger.info(f"  标准差: {stats['std']:.2f}")
        
        logger.info("=" * 60)


class PerformanceOptimizer:
    """
    性能优化器 - 集成所有优化功能
    使用 ic_sfp_gpu 环境进行 GPU 加速
    """
    
    def __init__(self, 
                 device: Optional[str] = None,
                 cache_dir: str = './cache',
                 max_cache_mb: int = 1024,
                 batch_size: int = 32):
        """
        初始化性能优化器
        
        Args:
            device: GPU 设备
            cache_dir: 缓存目录
            max_cache_mb: 最大缓存大小
            batch_size: 批大小
        """
        self.gpu = GPUAccelerator(device)
        self.cache = SmartCache(cache_dir, max_cache_mb)
        self.batch_processor = BatchProcessor(batch_size)
        self.monitor = PerformanceMonitor()
        
        logger.info("=" * 60)
        logger.info("🚀 性能优化器已初始化 (使用 ic_sfp_gpu 环境)")
        logger.info("=" * 60)
        logger.info(f"GPU: {self.gpu.device}")
        logger.info(f"缓存: {cache_dir}")
        logger.info(f"批大小: {batch_size}")
        logger.info("=" * 60)
    
    def optimize_causal_discovery(self, 
                                  data: np.ndarray,
                                  method: str = 'granger',
                                  use_cache: bool = True,
                                  **kwargs) -> np.ndarray:
        """
        优化的因果发现计算
        
        Args:
            data: 输入数据
            method: 方法 ('granger', 'correlation')
            use_cache: 是否使用缓存
            **kwargs: 其他参数
        
        Returns:
            因果图矩阵
        """
        # 生成缓存键
        cache_key = self.cache._get_cache_key(data.tobytes(), method, **kwargs)
        
        # 检查缓存
        if use_cache:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.info("✅ 使用缓存结果")
                return cached_result
        
        # 开始监控
        self.monitor.start()
        
        # 执行计算
        if method == 'granger':
            max_lag = kwargs.get('max_lag', 5)
            result = self.gpu.parallel_granger_test(data, max_lag)
        elif method == 'correlation':
            result = self.gpu.compute_correlation_matrix(data)
        else:
            raise ValueError(f"未知方法: {method}")
        
        # 记录性能
        self.monitor.record()
        
        # 保存到缓存
        if use_cache:
            self.cache.set(cache_key, result)
        
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'gpu': self.gpu.get_memory_usage(),
            'cache': self.cache.get_stats(),
            'performance': self.monitor.get_summary()
        }
    
    def print_status(self):
        """打印系统状态"""
        status = self.get_system_status()
        
        logger.info("=" * 60)
        logger.info("系统状态")
        logger.info("=" * 60)
        
        # GPU 状态
        logger.info("GPU/CPU 内存:")
        for key, value in status['gpu'].items():
            logger.info(f"  {key}: {value:.2f}")
        
        # 缓存状态
        logger.info("\n缓存统计:")
        for key, value in status['cache'].items():
            logger.info(f"  {key}: {value:.2f}" if isinstance(value, float) else f"  {key}: {value}")
        
        logger.info("=" * 60)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试性能优化器
    logger.info("开始测试性能优化器...")
    
    # 创建优化器
    optimizer = PerformanceOptimizer(
        cache_dir='./test_cache',
        max_cache_mb=512,
        batch_size=32
    )
    
    # 生成测试数据
    logger.info("生成测试数据...")
    np.random.seed(42)
    test_data = np.random.randn(1000, 50)  # 1000 samples, 50 features
    
    # 测试 GPU 加速的相关系数计算
    logger.info("\n测试 1: GPU 加速相关系数计算")
    start = time.time()
    corr_matrix = optimizer.optimize_causal_discovery(test_data, method='correlation')
    elapsed = time.time() - start
    logger.info(f"✅ 完成! 耗时: {elapsed:.4f}s")
    logger.info(f"   结果形状: {corr_matrix.shape}")
    
    # 测试缓存
    logger.info("\n测试 2: 缓存系统")
    start = time.time()
    corr_matrix_cached = optimizer.optimize_causal_discovery(test_data, method='correlation')
    elapsed_cached = time.time() - start
    logger.info(f"✅ 完成! 耗时: {elapsed_cached:.4f}s")
    logger.info(f"   加速比: {elapsed / elapsed_cached:.2f}x")
    
    # 测试 Granger 因果检验
    logger.info("\n测试 3: GPU 加速 Granger 因果检验")
    start = time.time()
    granger_matrix = optimizer.optimize_causal_discovery(test_data, method='granger', max_lag=5)
    elapsed = time.time() - start
    logger.info(f"✅ 完成! 耗时: {elapsed:.4f}s")
    logger.info(f"   结果形状: {granger_matrix.shape}")
    
    # 打印系统状态
    logger.info("\n测试 4: 系统状态")
    optimizer.print_status()
    
    # 性能监控摘要
    logger.info("\n测试 5: 性能监控")
    optimizer.monitor.print_summary()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 所有测试完成!")
    logger.info("=" * 60)
