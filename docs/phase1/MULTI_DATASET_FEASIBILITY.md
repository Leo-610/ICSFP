# 多数据集统一股票预测系统 - 可行性分析与实施方案

**日期**: 2025-11-05  
**项目**: HCSF (Hybrid Causal Stock Forecasting)  
**分析对象**: GitHub描述的多数据集统一系统

---

## 📋 执行摘要

### 结论: ✅ **可以实现，但需要分阶段开发**

**当前状态**: 60%已完成  
**开发时间**: 2-3周全面实现  
**技术难度**: 中等  

---

## 🔍 现状分析

### 已有基础 ✅

| 组件 | 状态 | 完成度 | 说明 |
|------|------|--------|------|
| **Main.py** | ✅ 存在 | 80% | 基础框架已有,需扩展命令行参数 |
| **Model.py** | ✅ 完整 | 100% | 支持因果图输入,架构完善 |
| **Executor.py** | ✅ 完整 | 100% | 训练执行逻辑完善 |
| **ConfigLoader.py** | ✅ 完整 | 100% | 配置管理系统完善 |
| **Granger因果** | ✅ 完整 | 100% | granger_causality.py (318行) |
| **CUTS+算法** | ✅ 完整 | 100% | cuts_plus.py (448行) |
| **DataPipe** | ✅ 完整 | 100% | 数据加载管道完善 |
| **API服务** | ✅ 完整 | 100% | Flask API已部署 |

### 缺失组件 ❌

| 组件 | 状态 | 优先级 | 开发时间 |
|------|------|--------|---------|
| **dataset_manager.py** | ❌ 不存在 | 高 | 2天 |
| **unified_data_loader.py** | ❌ 不存在 | 高 | 3天 |
| **causal_discovery_manager.py** | ❌ 不存在 | 中 | 2天 |
| **transfer_entropy.py** | ⚠️ TODO标记 | 中 | 2天 |
| **多数据集配置文件** | ❌ 不存在 | 中 | 1天 |
| **命令行接口扩展** | ❌ 不存在 | 高 | 1天 |

**总体完成度**: 60%

---

## ✅ 可行性评估

### 技术可行性: ⭐⭐⭐⭐⭐ (5/5)

**理由**:
1. ✅ 核心算法已实现 (Granger, CUTS+)
2. ✅ 模型架构支持因果图
3. ✅ DataPipe已支持多种数据格式
4. ✅ 配置系统灵活可扩展
5. ✅ Python生态完善 (argparse, OmegaConf等)

### 工程可行性: ⭐⭐⭐⭐☆ (4/5)

**理由**:
1. ✅ 模块化设计良好
2. ✅ 代码质量高
3. ⚠️ 需要重构部分硬编码路径
4. ⚠️ 需要统一数据格式规范

### 时间可行性: ⭐⭐⭐☆☆ (3/5)

**全面实现**: 2-3周  
**核心功能**: 1周  
**基础可用**: 3天  

---

## 🗺️ 实施路线图

### 阶段1: 核心基础 (3天) 🚀

**目标**: 实现基本的多数据集切换功能

#### Day 1: 数据集管理器
```python
# dataset_manager.py
class DatasetManager:
    DATASETS = {
        'ACL18': {
            'name': 'ACL18',
            'stocks': 88,
            'date_range': ('2014-01-01', '2016-01-01'),
            'price_path': 'data/cikm18/price/preprocessed',
            'text_path': 'data/cikm18/tweet/preprocessed',
            'description': 'ACL 2018 Stock Dataset'
        },
        'CMIN-CN': {
            'name': 'CMIN-CN',
            'stocks': 88,  # 当前
            'date_range': ('2015-01-01', '2017-12-31'),
            'price_path': 'data/cmin-cn/price/preprocessed',
            'text_path': 'data/cmin-cn/news/preprocessed',
            'description': 'CMIN Chinese Stock Dataset'
        }
    }
    
    def get_dataset(self, name):
        """获取数据集配置"""
        return self.DATASETS.get(name)
    
    def list_datasets(self):
        """列出所有可用数据集"""
        for name, info in self.DATASETS.items():
            print(f"{name}: {info['description']}")
```

**预期成果**:
- ✅ 数据集注册中心
- ✅ 配置统一管理
- ✅ 路径自动解析

#### Day 2: 命令行接口
```python
# Main.py 扩展
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    
    # 数据集选择
    parser.add_argument('--dataset', type=str, default='ACL18',
                        choices=['ACL18', 'CMIN-CN'],
                        help='Dataset to use')
    
    # 运行模式
    parser.add_argument('--mode', type=str, default='train',
                        choices=['train', 'test', 'eval'],
                        help='Run mode')
    
    # 因果发现方法
    parser.add_argument('--causal_method', type=str, default='granger',
                        choices=['granger', 'cuts', 'transfer_entropy', 'none'],
                        help='Causal discovery method')
    
    # 训练参数
    parser.add_argument('--epochs', type=int, default=15)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=0.001)
    
    # 设备选择
    parser.add_argument('--device', type=str, default='auto',
                        choices=['auto', 'cuda', 'cpu'])
    
    # 其他参数
    parser.add_argument('--lag', type=int, default=5)
    parser.add_argument('--checkpoint', type=str, default=None)
    parser.add_argument('--list_datasets', action='store_true')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.list_datasets:
        DatasetManager().list_datasets()
        return
    
    # 加载数据集配置
    dm = DatasetManager()
    dataset_config = dm.get_dataset(args.dataset)
    
    # 设置设备
    device = setup_device(args.device)
    
    # 加载因果图
    graph = load_or_compute_causal_graph(
        dataset_config,
        method=args.causal_method,
        lag=args.lag
    )
    
    # 创建模型
    model = Model(graph=graph)
    
    # 运行训练/测试
    if args.mode == 'train':
        executor.train_and_dev()
    elif args.mode == 'test':
        executor.restore_and_test()
```

**预期成果**:
- ✅ `python Main.py --dataset ACL18 --mode train`
- ✅ `python Main.py --list_datasets`
- ✅ `python Main.py --causal_method cuts`

#### Day 3: 统一数据加载器
```python
# unified_data_loader.py
class UnifiedDataLoader:
    def __init__(self, dataset_config):
        self.config = dataset_config
        self.price_path = dataset_config['price_path']
        self.text_path = dataset_config['text_path']
    
    def load_data(self, split='train'):
        """统一加载不同数据集"""
        # 动态适配不同格式
        if self.config['name'] == 'ACL18':
            return self._load_acl18(split)
        elif self.config['name'] == 'CMIN-CN':
            return self._load_cmin_cn(split)
    
    def _load_acl18(self, split):
        # ACL18格式加载逻辑
        pass
    
    def _load_cmin_cn(self, split):
        # CMIN-CN格式加载逻辑
        pass
```

**预期成果**:
- ✅ 统一数据接口
- ✅ 自动格式适配
- ✅ 兼容现有DataPipe

---

### 阶段2: 因果发现增强 (4天) 🔬

#### Day 4-5: 因果发现管理器
```python
# causal_discovery_manager.py
class CausalDiscoveryManager:
    def __init__(self, method='granger', device='cuda'):
        self.method = method
        self.device = device
        self.cache = {}
    
    def discover_causal_graph(self, data, stock_names, **kwargs):
        """统一的因果发现接口"""
        cache_key = self._get_cache_key(data, kwargs)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self.method == 'granger':
            graph = self._granger_discovery(data, **kwargs)
        elif self.method == 'cuts':
            graph = self._cuts_discovery(data, **kwargs)
        elif self.method == 'transfer_entropy':
            graph = self._te_discovery(data, **kwargs)
        elif self.method == 'none':
            graph = None
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        self.cache[cache_key] = graph
        return graph
    
    def _granger_discovery(self, data, lag=5):
        from granger_causality import GrangerCausalityAnalyzer
        analyzer = GrangerCausalityAnalyzer(max_lags=lag)
        matrix, p_values = analyzer.compute_causality_matrix(data)
        return matrix
    
    def _cuts_discovery(self, data):
        import cuts_plus
        from compute_cuts_graph import build_graph_cuts
        return build_graph_cuts(data)
    
    def _te_discovery(self, data, lag=5):
        # 实现传递熵
        from transfer_entropy import TransferEntropyAnalyzer
        analyzer = TransferEntropyAnalyzer(lag=lag)
        return analyzer.compute_te_matrix(data)
```

#### Day 6-7: 传递熵实现
```python
# transfer_entropy.py
import numpy as np
from scipy.stats import entropy

class TransferEntropyAnalyzer:
    """传递熵因果发现"""
    
    def __init__(self, lag=5, bins=10):
        self.lag = lag
        self.bins = bins
    
    def compute_te_matrix(self, data, stock_names=None):
        """
        计算传递熵矩阵
        TE(Y→X) = H(X_t|X_{t-lag}) - H(X_t|X_{t-lag},Y_{t-lag})
        """
        T, N = data.shape
        te_matrix = np.zeros((N, N))
        
        for i in range(N):
            for j in range(N):
                if i != j:
                    te_matrix[i, j] = self._compute_te_pair(
                        data[:, i], data[:, j]
                    )
        
        # 归一化
        te_matrix = self._normalize_matrix(te_matrix)
        return te_matrix, {}
    
    def _compute_te_pair(self, X, Y):
        """计算X→Y的传递熵"""
        # 离散化
        X_disc = self._discretize(X)
        Y_disc = self._discretize(Y)
        
        # 构建历史序列
        X_past = X_disc[:-self.lag]
        Y_curr = Y_disc[self.lag:]
        Y_past = Y_disc[:-self.lag]
        
        # H(Y_t | Y_{t-lag})
        h1 = self._conditional_entropy(Y_curr, Y_past)
        
        # H(Y_t | Y_{t-lag}, X_{t-lag})
        h2 = self._conditional_entropy_joint(Y_curr, Y_past, X_past)
        
        # TE = H1 - H2
        te = h1 - h2
        return max(0, te)  # 传递熵非负
    
    def _discretize(self, x):
        """离散化时间序列"""
        return np.digitize(x, bins=np.linspace(x.min(), x.max(), self.bins))
    
    def _conditional_entropy(self, X, Y):
        """H(X|Y)"""
        # 使用scipy.stats.entropy实现
        pass
    
    def _normalize_matrix(self, matrix):
        """行归一化"""
        row_sums = matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        return matrix / row_sums
```

**预期成果**:
- ✅ 传递熵完整实现
- ✅ 3种因果方法可选
- ✅ 统一接口调用

---

### 阶段3: 多尺度扩展 (4天) 📊

#### Day 8-9: 多尺度分析
```python
# multiscale_views.py
import numpy as np
from scipy.fft import fft, fftfreq

def build_multiscale_views(data, top_k=3):
    """
    构建多尺度视图
    1. FFT频域分析提取主要周期
    2. 对每个周期下采样
    3. 计算技术指标和统计特征
    """
    # 1. FFT分析
    periods = extract_main_periods(data, top_k)
    
    # 2. 生成多尺度视图
    views = {}
    for period in periods:
        scale_data = downsample(data, period)
        
        # 计算技术指标
        tech_features = compute_technical_indicators(scale_data)
        
        # 计算统计特征
        stat_features = compute_statistical_features(scale_data)
        
        views[period] = {
            'data': scale_data,
            'tech': tech_features,
            'stat': stat_features
        }
    
    return {
        'periods': periods,
        'views': views
    }

def extract_main_periods(data, top_k=3):
    """FFT频域分析提取主要周期"""
    T, N = data.shape
    
    # 对每个股票做FFT
    periods_list = []
    for i in range(N):
        # FFT变换
        fft_vals = fft(data[:, i])
        freqs = fftfreq(T)
        
        # 找功率谱峰值
        power = np.abs(fft_vals)**2
        peak_indices = np.argsort(power)[-top_k:]
        
        # 转换为周期
        peak_freqs = freqs[peak_indices]
        periods = 1 / (peak_freqs + 1e-10)
        periods_list.append(periods)
    
    # 取中位数作为代表周期
    representative_periods = np.median(periods_list, axis=0)
    return sorted(representative_periods)

def compute_technical_indicators(data):
    """计算技术指标"""
    return {
        'MA': moving_average(data),
        'RSI': relative_strength_index(data),
        'MACD': macd(data),
        'BB': bollinger_bands(data)
    }
```

#### Day 10-11: 多尺度因果融合
```python
# multiscale_causal.py
def compute_multiscale_causal_graph(data, method='granger', top_k=3):
    """
    多尺度因果发现
    1. 在不同尺度上计算因果图
    2. 融合多尺度结果
    """
    # 构建多尺度视图
    views = build_multiscale_views(data, top_k)
    
    # 在每个尺度上发现因果
    causal_graphs = []
    for period, view_data in views['views'].items():
        graph = discover_causal_at_scale(
            view_data['data'],
            method=method
        )
        causal_graphs.append(graph)
    
    # 融合策略
    fused_graph = fuse_causal_graphs(
        causal_graphs,
        strategy='weighted'
    )
    
    return fused_graph

def fuse_causal_graphs(graphs, strategy='weighted'):
    """融合多尺度因果图"""
    if strategy == 'weighted':
        # 加权平均 (长周期权重更高)
        weights = np.array([1.0, 0.7, 0.5])
        weights = weights / weights.sum()
        
        fused = sum(w * g for w, g in zip(weights, graphs))
        
    elif strategy == 'attention':
        # 注意力机制融合
        fused = attention_fusion(graphs)
        
    elif strategy == 'max':
        # 取最大值
        fused = np.maximum.reduce(graphs)
    
    return fused
```

**预期成果**:
- ✅ FFT多尺度分析
- ✅ 技术指标计算
- ✅ 多尺度因果融合

---

### 阶段4: 配置与测试 (3天) 🧪

#### Day 12: 配置文件生成
```python
# generate_dataset_configs.py
def generate_acl18_config():
    config = {
        'dataset': {
            'name': 'ACL18',
            'description': 'ACL 2018 Stock Dataset',
            'stocks': 88,
            'date_range': {
                'train_start': '2014-01-01',
                'train_end': '2015-08-01',
                'dev_start': '2015-08-01',
                'dev_end': '2015-10-01',
                'test_start': '2015-10-01',
                'test_end': '2016-01-01'
            }
        },
        'paths': {
            'data': 'data/cikm18/',
            'price': 'cikm18/price/preprocessed',
            'text': 'cikm18/tweet/preprocessed'
        },
        'model': {
            'batch_size': 32,
            'learning_rate': 0.001,
            'epochs': 15
        },
        'causal': {
            'method': 'granger',
            'lag': 5,
            'significance': 0.05
        }
    }
    
    with open('config_acl18_unified.yml', 'w') as f:
        yaml.dump(config, f)

# 自动生成所有数据集配置
generate_acl18_config()
generate_cmin_cn_config()
```

#### Day 13-14: 集成测试
```python
# test_multi_dataset.py
def test_acl18():
    """测试ACL18数据集"""
    cmd = "python Main.py --dataset ACL18 --mode train --epochs 2"
    result = subprocess.run(cmd, shell=True, capture_output=True)
    assert result.returncode == 0

def test_cmin_cn():
    """测试CMIN-CN数据集"""
    cmd = "python Main.py --dataset CMIN-CN --mode train --epochs 2"
    result = subprocess.run(cmd, shell=True, capture_output=True)
    assert result.returncode == 0

def test_causal_methods():
    """测试不同因果方法"""
    methods = ['granger', 'cuts', 'transfer_entropy', 'none']
    for method in methods:
        cmd = f"python Main.py --dataset ACL18 --causal_method {method}"
        result = subprocess.run(cmd, shell=True, capture_output=True)
        assert result.returncode == 0
```

---

## 📊 实施优先级

### 🔥 高优先级 (必须实现)
1. ✅ dataset_manager.py - 数据集管理
2. ✅ 命令行参数扩展 - 用户接口
3. ✅ unified_data_loader.py - 数据加载统一
4. ✅ causal_discovery_manager.py - 因果发现统一接口

### ⚡ 中优先级 (重要但非紧急)
5. ✅ transfer_entropy.py - 传递熵实现
6. ✅ 配置文件生成器 - 自动化配置
7. ✅ 多尺度分析 - 性能提升

### 🌟 低优先级 (锦上添花)
8. ⭕ 图神经网络 (GNN) - 高级建模
9. ⭕ Transformer模型 - 时序建模
10. ⭕ 实时预测流 - 在线服务

---

## 💰 成本估算

### 开发成本
- **人力**: 1人 × 2-3周 = 10-15天
- **复杂度**: 中等 (基础已有60%)
- **风险**: 低 (核心算法已验证)

### 资源需求
- **GPU**: 已有 (CUDA支持)
- **存储**: 数据集 <10GB
- **依赖**: 无新增大型依赖

---

## 🎯 预期成果

### 功能成果
```bash
# 1. 数据集切换
python Main.py --dataset ACL18 --mode train
python Main.py --dataset CMIN-CN --mode test

# 2. 因果方法切换
python Main.py --causal_method granger
python Main.py --causal_method cuts
python Main.py --causal_method transfer_entropy

# 3. 多尺度分析
python Main.py --use_multi_scale --top_k 3

# 4. 列出数据集
python Main.py --list_datasets

# 5. 完整示例
python Main.py \
    --dataset ACL18 \
    --mode train \
    --causal_method granger \
    --lag 5 \
    --epochs 15 \
    --batch_size 32 \
    --device cuda
```

### 性能成果
- ✅ 支持2+数据集 (ACL18, CMIN-CN)
- ✅ 3种因果方法 (Granger, CUTS+, Transfer Entropy)
- ✅ 多尺度分析 (FFT + 多周期)
- ✅ 灵活配置 (命令行 + YAML)
- ✅ 统一接口 (一条命令运行)

---

## ⚠️ 风险与挑战

### 技术风险 (低)
1. **数据格式差异**: 
   - 风险: 不同数据集格式不同
   - 缓解: 统一数据加载器 + 格式转换

2. **性能瓶颈**:
   - 风险: 多尺度分析计算量大
   - 缓解: GPU加速 + 批处理优化

### 工程风险 (中)
3. **配置复杂度**:
   - 风险: 太多参数难以管理
   - 缓解: 合理默认值 + 配置模板

4. **兼容性问题**:
   - 风险: 新代码与旧代码冲突
   - 缓解: 充分测试 + 版本控制

---

## ✅ 最终结论

### 可行性评分: 9/10

**YES, 完全可以实现！**

**理由**:
1. ✅ **基础扎实**: 60%已完成
2. ✅ **技术成熟**: 核心算法已验证
3. ✅ **架构合理**: 模块化设计良好
4. ✅ **时间可控**: 2-3周完成
5. ✅ **风险可控**: 主要是工程实现

### 建议实施策略

**快速原型** (3天):
```bash
# 最小可行产品 (MVP)
1. dataset_manager.py (基础版)
2. Main.py命令行参数
3. 2个数据集支持 (ACL18, CMIN-CN)
```

**完整版本** (2周):
```bash
1. 所有4个缺失组件
2. 传递熵实现
3. 多尺度分析
4. 完整测试
```

**增强版本** (3周):
```bash
+ 更多数据集
+ 更多因果方法
+ 性能优化
+ 文档完善
```

---

## 📝 行动计划

### 立即开始 (今天)
1. ✅ 创建 dataset_manager.py 框架
2. ✅ 扩展 Main.py 命令行参数
3. ✅ 测试基础功能

### 本周内 (3天)
4. ✅ 实现 unified_data_loader.py
5. ✅ 实现 causal_discovery_manager.py
6. ✅ 基础集成测试

### 下周 (5天)
7. ✅ 传递熵实现
8. ✅ 多尺度分析
9. ✅ 配置文件生成
10. ✅ 完整测试

---

**总结**: 这个项目**完全可行**,建议**分阶段实施**,先实现核心功能,再逐步完善高级特性。基于现有60%的基础,2-3周内可以实现一个功能完整的多数据集统一系统！🚀
