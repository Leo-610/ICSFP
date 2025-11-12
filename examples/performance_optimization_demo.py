"""
性能优化演示 - 集成到因果发现管理器
展示如何使用 ic_sfp_gpu 环境进行 GPU 加速和性能优化
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import time
import logging
from utils.performance_optimizer import PerformanceOptimizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_basic_usage():
    """演示基本用法"""
    logger.info("=" * 70)
    logger.info("演示 1: 基本用法")
    logger.info("=" * 70)
    
    # 创建优化器
    optimizer = PerformanceOptimizer(
        cache_dir='./demo_cache',
        max_cache_mb=100,
        batch_size=32
    )
    
    # 生成测试数据
    logger.info("\n生成测试数据: 1000 samples × 30 features")
    np.random.seed(42)
    data = np.random.randn(1000, 30)
    
    # 测试相关系数计算
    logger.info("\n测试 GPU 加速相关系数计算...")
    start = time.time()
    corr_matrix = optimizer.optimize_causal_discovery(data, method='correlation')
    elapsed = time.time() - start
    
    logger.info(f"✅ 完成! 耗时: {elapsed:.4f}s")
    logger.info(f"   结果形状: {corr_matrix.shape}")
    logger.info(f"   非零元素: {np.count_nonzero(corr_matrix > 0.3)}")
    
    # 测试缓存效果
    logger.info("\n测试缓存效果...")
    start = time.time()
    corr_matrix_cached = optimizer.optimize_causal_discovery(data, method='correlation')
    elapsed_cached = time.time() - start
    
    logger.info(f"✅ 缓存命中! 耗时: {elapsed_cached:.4f}s")
    if elapsed_cached > 0:
        logger.info(f"   加速比: {elapsed / elapsed_cached:.2f}x")
    else:
        logger.info(f"   加速比: ∞ (缓存瞬时命中)")
    
    # 打印系统状态
    logger.info("\n系统状态:")
    optimizer.print_status()
    
    return optimizer


def demo_granger_causality():
    """演示 Granger 因果检验"""
    logger.info("\n" + "=" * 70)
    logger.info("演示 2: GPU 加速 Granger 因果检验")
    logger.info("=" * 70)
    
    optimizer = PerformanceOptimizer(
        cache_dir='./demo_cache',
        max_cache_mb=100,
        batch_size=32
    )
    
    # 生成时间序列数据
    logger.info("\n生成时间序列数据: 500 samples × 20 features")
    np.random.seed(42)
    
    # 创建具有因果关系的数据
    n_samples = 500
    n_features = 20
    data = np.zeros((n_samples, n_features))
    
    # 生成基础时间序列
    for i in range(n_features):
        data[:, i] = np.cumsum(np.random.randn(n_samples) * 0.1)
    
    # 添加一些因果关系
    # X1 -> X2 (滞后1)
    data[1:, 1] += 0.5 * data[:-1, 0]
    # X2 -> X3 (滞后2)
    data[2:, 2] += 0.3 * data[:-2, 1]
    # X0 -> X5 (滞后3)
    data[3:, 5] += 0.4 * data[:-3, 0]
    
    # 运行 Granger 检验
    logger.info("\n运行 GPU 加速 Granger 检验 (max_lag=5)...")
    start = time.time()
    causal_matrix = optimizer.optimize_causal_discovery(
        data, 
        method='granger', 
        max_lag=5,
        use_cache=False
    )
    elapsed = time.time() - start
    
    logger.info(f"✅ 完成! 耗时: {elapsed:.4f}s")
    logger.info(f"   因果图形状: {causal_matrix.shape}")
    logger.info(f"   检测到的因果关系: {np.count_nonzero(causal_matrix > 0.2)}")
    
    # 显示最强的因果关系
    logger.info("\n最强的 5 个因果关系:")
    flat_indices = np.argsort(causal_matrix.flatten())[::-1]
    for idx in flat_indices[:5]:
        i = idx // n_features
        j = idx % n_features
        if i != j:
            strength = causal_matrix[i, j]
            logger.info(f"   X{j} -> X{i}: {strength:.4f}")
    
    return causal_matrix


def demo_batch_processing():
    """演示批处理"""
    logger.info("\n" + "=" * 70)
    logger.info("演示 3: 批处理优化")
    logger.info("=" * 70)
    
    optimizer = PerformanceOptimizer(
        cache_dir='./demo_cache',
        max_cache_mb=100,
        batch_size=16
    )
    
    # 生成多个数据集
    logger.info("\n生成 10 个数据集...")
    datasets = []
    for i in range(10):
        data = np.random.randn(200, 15)
        datasets.append((f"dataset_{i}", data))
    
    # 批量处理
    logger.info("\n批量处理因果发现...")
    start = time.time()
    
    results = []
    for name, data in datasets:
        causal_matrix = optimizer.optimize_causal_discovery(
            data, 
            method='correlation',
            use_cache=True
        )
        results.append((name, causal_matrix))
    
    elapsed = time.time() - start
    
    logger.info(f"✅ 完成! 总耗时: {elapsed:.4f}s")
    logger.info(f"   平均每个数据集: {elapsed / len(datasets):.4f}s")
    
    # 统计结果
    logger.info("\n结果统计:")
    for name, matrix in results:
        edges = np.count_nonzero(matrix > 0.3)
        logger.info(f"   {name}: {edges} 条边")
    
    return results


def demo_memory_management():
    """演示内存管理"""
    logger.info("\n" + "=" * 70)
    logger.info("演示 4: 内存管理和缓存驱逐")
    logger.info("=" * 70)
    
    optimizer = PerformanceOptimizer(
        cache_dir='./demo_cache',
        max_cache_mb=50,  # 限制为 50MB
        batch_size=32
    )
    
    # 生成大量数据
    logger.info("\n生成并处理大量数据...")
    
    for i in range(20):
        # 生成随机大小的数据
        n_samples = np.random.randint(200, 500)
        n_features = np.random.randint(10, 30)
        data = np.random.randn(n_samples, n_features)
        
        # 处理数据
        causal_matrix = optimizer.optimize_causal_discovery(
            data,
            method='correlation',
            use_cache=True
        )
        
        # 每 5 次打印一次状态
        if (i + 1) % 5 == 0:
            logger.info(f"\n处理第 {i + 1} 个数据集")
            stats = optimizer.cache.get_stats()
            logger.info(f"   内存缓存: {stats['memory_items']} 项, "
                       f"{stats['memory_size_mb']:.2f} MB")
            logger.info(f"   磁盘缓存: {stats['disk_items']} 项, "
                       f"{stats['disk_size_mb']:.2f} MB")
    
    # 最终状态
    logger.info("\n最终系统状态:")
    optimizer.print_status()


def demo_performance_comparison():
    """演示性能对比: GPU vs CPU"""
    logger.info("\n" + "=" * 70)
    logger.info("演示 5: GPU vs CPU 性能对比")
    logger.info("=" * 70)
    
    # 生成大规模数据
    logger.info("\n生成大规模数据: 2000 samples × 50 features")
    np.random.seed(42)
    data = np.random.randn(2000, 50)
    
    # GPU 加速
    logger.info("\n使用 GPU 加速...")
    optimizer_gpu = PerformanceOptimizer(device='cuda' if is_gpu_available() else 'cpu')
    start = time.time()
    result_gpu = optimizer_gpu.optimize_causal_discovery(
        data, 
        method='correlation',
        use_cache=False
    )
    time_gpu = time.time() - start
    logger.info(f"✅ GPU 耗时: {time_gpu:.4f}s")
    
    # CPU 计算
    logger.info("\n使用 CPU 计算...")
    optimizer_cpu = PerformanceOptimizer(device='cpu')
    start = time.time()
    result_cpu = optimizer_cpu.optimize_causal_discovery(
        data, 
        method='correlation',
        use_cache=False
    )
    time_cpu = time.time() - start
    logger.info(f"✅ CPU 耗时: {time_cpu:.4f}s")
    
    # 性能对比
    logger.info("\n性能对比:")
    logger.info(f"   GPU: {time_gpu:.4f}s")
    logger.info(f"   CPU: {time_cpu:.4f}s")
    if time_cpu > time_gpu:
        speedup = time_cpu / time_gpu
        logger.info(f"   加速比: {speedup:.2f}x (GPU 更快)")
    else:
        slowdown = time_gpu / time_cpu
        logger.info(f"   CPU 更快: {slowdown:.2f}x (可能是小数据集)")
    
    # 验证结果一致性
    diff = np.abs(result_gpu - result_cpu).max()
    logger.info(f"\n结果差异: {diff:.6f}")
    if diff < 0.01:
        logger.info("   ✅ GPU 和 CPU 结果一致")
    else:
        logger.info("   ⚠️ GPU 和 CPU 结果存在差异")


def is_gpu_available():
    """检查 GPU 是否可用"""
    import torch
    return torch.cuda.is_available()


def main():
    """主函数"""
    logger.info("=" * 70)
    logger.info("性能优化演示 - 使用 ic_sfp_gpu 环境")
    logger.info("=" * 70)
    
    # 检查 GPU
    if is_gpu_available():
        import torch
        logger.info(f"✅ GPU 可用: {torch.cuda.get_device_name(0)}")
        logger.info(f"   GPU 内存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        logger.info("⚠️ GPU 不可用，使用 CPU 模式")
    
    try:
        # 运行所有演示
        demo_basic_usage()
        demo_granger_causality()
        demo_batch_processing()
        demo_memory_management()
        demo_performance_comparison()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ 所有演示完成!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"演示过程中出错: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
