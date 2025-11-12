# Performance Optimization Guide

## 概述

Phase 3 Task 4 已完成性能优化集成,使用 `ic_sfp_gpu` 环境提供 GPU 加速、智能缓存、批处理等功能。

## 环境要求

- **Python**: 3.10.19
- **Conda 环境**: `ic_sfp_gpu`
- **GPU**: NVIDIA RTX 4060 (8.59 GB)
- **PyTorch**: 2.5.1 + CUDA
- **依赖包**: psutil, joblib, numpy

## 核心功能

### 1. GPU 加速器 (GPUAccelerator)

使用 PyTorch GPU 加速计算:

```python
from utils.performance_optimizer import GPUAccelerator

# 初始化
gpu = GPUAccelerator(device='cuda')  # 自动检测 GPU

# GPU 加速相关系数计算
data = np.random.randn(1000, 50)
corr_matrix = gpu.compute_correlation_matrix(data)

# GPU 加速 Granger 因果检验
causal_matrix = gpu.parallel_granger_test(data, max_lag=5)

# 获取内存使用情况
memory_info = gpu.get_memory_usage()
```

**性能提升**:
- 相关系数计算: 1.12x (GPU vs CPU)
- 大规模数据集 (2000×50): GPU 更优

### 2. 智能缓存系统 (SmartCache)

多级缓存 (内存 + 磁盘压缩):

```python
from utils.performance_optimizer import SmartCache

# 初始化 (最大内存 100MB)
cache = SmartCache(cache_dir='./cache', max_memory_mb=100)

# 设置缓存 (自动压缩)
data = np.random.randn(1000, 100)
cache.set('my_key', data, compress=True)

# 获取缓存
cached_data = cache.get('my_key')

# 查看统计
stats = cache.get_stats()
print(f"命中率: {stats['hit_rate']:.2%}")
print(f"内存项数: {stats['memory_items']}")
print(f"磁盘项数: {stats['disk_items']}")
```

**特性**:
- LRU 驱逐策略
- gzip 压缩存储
- 命中率跟踪
- 加速比: 3.54x (重复查询)

### 3. 批处理器 (BatchProcessor)

智能批量处理:

```python
from utils.performance_optimizer import BatchProcessor

processor = BatchProcessor(batch_size=32, num_workers=4)

# 批量处理
data_list = [np.random.randn(100, 10) for _ in range(100)]
def process_fn(data):
    return np.mean(data)

results = processor.process_in_batches(data_list, process_fn)
```

### 4. 性能监控器 (PerformanceMonitor)

实时性能跟踪:

```python
from utils.performance_optimizer import PerformanceMonitor

monitor = PerformanceMonitor()

# 开始监控
monitor.start()

# 执行任务
for _ in range(10):
    # ... 计算 ...
    monitor.record()

# 获取摘要
summary = monitor.get_summary()
monitor.print_summary()
```

**监控指标**:
- CPU 使用率
- 内存占用
- GPU 内存分配
- 执行时间

### 5. 性能优化器 (PerformanceOptimizer)

集成所有功能的统一接口:

```python
from utils.performance_optimizer import PerformanceOptimizer

# 初始化优化器
optimizer = PerformanceOptimizer(
    device='cuda',           # GPU 加速
    cache_dir='./cache',     # 缓存目录
    max_cache_mb=1024,       # 最大缓存 1GB
    batch_size=32            # 批大小
)

# 优化的因果发现
data = np.random.randn(1000, 30)

# 方法 1: 相关系数 (快速)
corr_graph = optimizer.optimize_causal_discovery(
    data, 
    method='correlation',
    use_cache=True
)

# 方法 2: Granger 因果检验 (精确)
granger_graph = optimizer.optimize_causal_discovery(
    data,
    method='granger',
    max_lag=5,
    use_cache=True
)

# 查看系统状态
optimizer.print_status()
```

## 集成示例

### 与因果发现管理器集成

```python
from causal.causal_discovery_manager import CausalDiscoveryManager
from utils.performance_optimizer import PerformanceOptimizer

# 初始化
causal_mgr = CausalDiscoveryManager()
optimizer = PerformanceOptimizer(device='cuda', cache_dir='./cache')

# 加载数据
data = causal_mgr.load_stock_data(['AAPL', 'GOOGL', 'MSFT'])

# 使用优化器加速因果发现
causal_graph = optimizer.optimize_causal_discovery(
    data,
    method='granger',
    max_lag=5
)

# 保存结果
causal_mgr.save_graph(causal_graph, 'optimized_graph.npy')
```

### 与 UnifiedPipeline 集成

```python
from unified_pipeline import UnifiedPipeline
from utils.performance_optimizer import PerformanceOptimizer

# 创建管道
pipeline = UnifiedPipeline(config_path='config.yml')

# 添加性能优化器
optimizer = PerformanceOptimizer(device='cuda')
pipeline.optimizer = optimizer

# 运行端到端流程
results = pipeline.run_end_to_end(
    method='granger',
    use_optimizer=True,  # 启用优化
    use_cache=True
)
```

## 性能基准测试

### 测试环境
- GPU: NVIDIA RTX 4060 Laptop GPU (8.59 GB)
- CPU: Intel Core (详细型号待补充)
- RAM: 16 GB
- Python: 3.10.19
- PyTorch: 2.5.1 + CUDA

### 测试结果

#### 1. 相关系数计算 (1000×30)
- **GPU**: 0.0955s
- **缓存命中**: 0.0000s (∞ 加速)
- **加速比**: 3.54x (重复查询)

#### 2. Granger 因果检验 (500×20, max_lag=5)
- **GPU**: 0.4292s
- **检测到因果关系**: 313 条边

#### 3. 批量处理 (10个数据集, 200×15)
- **总耗时**: 0.0495s
- **平均每个**: 0.0050s

#### 4. 大规模数据 (2000×50)
- **GPU**: 0.0196s
- **CPU**: 0.0218s
- **加速比**: 1.12x (GPU 更快)

#### 5. 内存管理
- **20个数据集处理**
- **内存缓存**: 0.03 MB (20 项)
- **磁盘缓存**: 0.04 MB (31 项)
- **缓存命中率**: 100%

## 测试套件

运行测试:

```bash
# 激活环境
conda activate ic_sfp_gpu

# 运行单元测试
python tests/test_performance_optimizer.py

# 运行演示
python examples/performance_optimization_demo.py
```

**测试覆盖**:
- GPU 加速器: 4 个测试
- 智能缓存: 4 个测试
- 批处理器: 2 个测试
- 性能监控: 3 个测试
- 集成优化器: 2 个测试
- **总计**: 15/15 通过 ✅

## 最佳实践

### 1. 选择合适的方法

```python
# 快速原型: 使用相关系数
graph_fast = optimizer.optimize_causal_discovery(
    data, method='correlation'
)

# 精确分析: 使用 Granger 检验
graph_precise = optimizer.optimize_causal_discovery(
    data, method='granger', max_lag=5
)
```

### 2. 合理使用缓存

```python
# 启用缓存 (推荐用于重复查询)
result = optimizer.optimize_causal_discovery(
    data, method='granger', use_cache=True
)

# 禁用缓存 (数据变化频繁)
result = optimizer.optimize_causal_discovery(
    data, method='granger', use_cache=False
)
```

### 3. 监控系统资源

```python
# 定期检查内存使用
memory_info = optimizer.gpu.get_memory_usage()
if memory_info['gpu_free_gb'] < 1.0:
    torch.cuda.empty_cache()  # 清理 GPU 内存

# 查看缓存统计
stats = optimizer.cache.get_stats()
if stats['memory_size_mb'] > 800:
    optimizer.cache.clear()  # 清理缓存
```

### 4. 批量处理大数据集

```python
# 处理多个股票
stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', ...]
results = {}

for stock in stocks:
    data = load_stock_data(stock)
    graph = optimizer.optimize_causal_discovery(
        data, method='correlation', use_cache=True
    )
    results[stock] = graph
```

## 故障排查

### GPU 内存不足

```python
# 错误: RuntimeError: CUDA out of memory
# 解决方案 1: 减小数据规模
data_small = data[:500]  # 使用部分数据

# 解决方案 2: 清理 GPU 缓存
torch.cuda.empty_cache()

# 解决方案 3: 使用 CPU
optimizer = PerformanceOptimizer(device='cpu')
```

### 缓存占用过大

```python
# 查看缓存大小
stats = optimizer.cache.get_stats()
print(f"磁盘缓存: {stats['disk_size_mb']:.2f} MB")

# 清理缓存
optimizer.cache.clear()

# 减小缓存限制
optimizer = PerformanceOptimizer(max_cache_mb=512)
```

### GPU 不可用

```python
import torch

# 检查 GPU
if not torch.cuda.is_available():
    print("⚠️ GPU 不可用")
    print("解决方案:")
    print("1. 检查 CUDA 安装")
    print("2. 使用 CPU 模式: device='cpu'")
    print("3. 重新安装 PyTorch with CUDA")
```

## 下一步

- [ ] **Task 5**: API 统一 - 集成性能优化器到 FastAPI 接口
- [ ] **Task 6**: 可视化仪表板 - 实时监控性能指标
- [ ] **Task 7**: 模型训练工作流 - GPU 加速训练
- [ ] **Task 8**: 全面测试 - 性能压力测试

## 参考

- PyTorch 官方文档: https://pytorch.org/docs/
- CUDA 编程指南: https://docs.nvidia.com/cuda/
- 性能优化最佳实践: [PERFORMANCE_BEST_PRACTICES.md](./PERFORMANCE_BEST_PRACTICES.md)

---

**更新日期**: 2025-11-12  
**版本**: 1.0.0  
**作者**: ICSFP Team
