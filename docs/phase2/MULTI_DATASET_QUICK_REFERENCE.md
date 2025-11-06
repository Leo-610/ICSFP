# 🚀 多数据集系统 - 快速参考手册

> **Version**: 2.0.0 | **Updated**: 2025-01-05

---

## 📋 快速命令

### 数据集管理

```bash
# 列出所有数据集
python Main.py --list_datasets

# 检查数据集状态
python Main.py --check_dataset ACL18
python Main.py --check_dataset CMIN-CN
python Main.py --check_dataset CIKM18

# 生成配置文件
python Main.py --generate_config ACL18
python Main.py --generate_config CMIN-CN
```

### 训练命令

```bash
# 基础训练 (使用默认ACL18数据集)
python Main.py

# 指定数据集
python Main.py --dataset ACL18
python Main.py --dataset CMIN-CN
python Main.py --dataset CIKM18

# 指定因果方法
python Main.py --causal_method granger
python Main.py --causal_method cuts_plus
python Main.py --causal_method none

# 强制重新计算因果图
python Main.py --recompute_causal

# 自定义训练参数
python Main.py --epochs 20 --batch_size 64 --learning_rate 0.0005
```

### 运行模式

```bash
# 仅训练
python Main.py --mode train

# 仅测试
python Main.py --mode test

# 训练+测试
python Main.py --mode train_test
```

### 设备选择

```bash
# 自动选择 (默认)
python Main.py --device auto

# 强制使用GPU
python Main.py --device cuda

# 强制使用CPU
python Main.py --device cpu
```

---

## 🎯 常用组合

### 场景1: 快速验证
```bash
# 检查数据 + 快速训练
python Main.py --check_dataset ACL18
python Main.py --dataset ACL18 --epochs 2 --batch_size 16
```

### 场景2: 完整实验
```bash
# ACL18 + Granger + 完整训练
python Main.py --dataset ACL18 \
               --causal_method granger \
               --mode train_test \
               --epochs 15 \
               --device cuda
```

### 场景3: 对比实验
```bash
# 不同因果方法对比
python Main.py --causal_method granger --mode train_test
python Main.py --causal_method cuts_plus --recompute_causal --mode train_test
python Main.py --causal_method none --mode train_test
```

### 场景4: 多数据集对比
```bash
# 不同数据集对比
python Main.py --dataset ACL18 --mode train_test
python Main.py --dataset CMIN-CN --mode train_test
python Main.py --dataset CIKM18 --mode train_test
```

---

## 📊 可用数据集

| 数据集 | 描述 | 股票数 | 时间范围 | 命令 |
|--------|------|--------|----------|------|
| **ACL18** | 美股+推文 | 88 | 2014-2016 | `--dataset ACL18` |
| **CIKM18** | 美股+推文 | 38 | 2014-2016 | `--dataset CIKM18` |
| **CMIN-CN** | A股+微博 | 88 | 2015-2017 | `--dataset CMIN-CN` |

---

## 🔗 因果发现方法

| 方法 | 描述 | 命令 | 计算脚本 |
|------|------|------|----------|
| **granger** | Granger因果检验 (默认) | `--causal_method granger` | `python granger_causality.py` |
| **cuts_plus** | CUTS+神经网络方法 | `--causal_method cuts_plus` | `python compute_cuts_graph.py` |
| **transfer_entropy** | 传递熵 (计划中) | `--causal_method transfer_entropy` | TBD |
| **none** | 不使用因果图 | `--causal_method none` | N/A |

---

## ⚙️ 超参数参考

| 参数 | 默认值 | 范围 | 说明 |
|------|--------|------|------|
| `--epochs` | 15 | 1-100 | 训练轮数 |
| `--batch_size` | 32 | 8-256 | 批次大小 |
| `--learning_rate` | 0.001 | 0.0001-0.01 | 学习率 |
| `--seed` | 42 | 任意整数 | 随机种子 |

---

## 🔍 数据准备工具

```bash
# 准备CIKM18数据集
python download_cmin_dataset.py

# 检查数据完整性
python test_datapipe_cikm18.py

# 验证因果图
python verify_innovation_algorithms.py
```

---

## 🛠️ 因果图生成

```bash
# 生成Granger因果图
python granger_causality.py

# 生成CUTS+因果图
python compute_cuts_graph.py

# 强制重新计算
python Main.py --recompute_causal
```

---

## 📝 配置文件

### 自动生成
```bash
python Main.py --generate_config ACL18
# 生成: config_acl18.yml

python Main.py --generate_config CMIN-CN
# 生成: config_cmin-cn.yml
```

### 配置结构
```yaml
dataset:
  name: ACL18
  description: 88只美股 (2014-2016) + Twitter推文
  stocks: 88

dates:
  start: '2014-01-01'
  end: '2016-01-01'
  train_start: '2014-01-01'
  train_end: '2015-08-01'
  dev_start: '2015-08-01'
  dev_end: '2015-10-01'
  test_start: '2015-10-01'
  test_end: '2016-01-01'

paths:
  data: data/cikm18/
  price: cikm18/price/preprocessed
  tweet_preprocessed: cikm18/tweet/preprocessed

model:
  batch_size: 32
  learning_rate: 0.001
  n_epochs: 15
  max_n_days: 5
  max_n_msgs: 30
  max_n_words: 40

causal:
  method: granger
  max_lags: 5
  significance_level: 0.05
```

---

## ⚡ 性能建议

### GPU训练 (推荐)
```bash
# 使用GPU + 大批次
python Main.py --device cuda --batch_size 128
```

### CPU训练
```bash
# 使用CPU + 小批次
python Main.py --device cpu --batch_size 16
```

### 快速测试
```bash
# 少轮次 + 小批次
python Main.py --epochs 2 --batch_size 8
```

### 生产训练
```bash
# 多轮次 + 大批次 + GPU
python Main.py --epochs 50 --batch_size 128 --device cuda
```

---

## 🐛 常见问题

### Q1: 数据集未就绪
```bash
Error: 数据集未就绪!
  价格数据: ❌ (0 文件)
  文本数据: ❌ (0 目录)

# 解决方案:
python download_cmin_dataset.py
```

### Q2: 因果图未找到
```bash
Warning: Causal graph file not found: causal_graph.npy
💡 运行因果发现: python granger_causality.py

# 解决方案:
python granger_causality.py  # Granger方法
# 或
python compute_cuts_graph.py  # CUTS+方法
```

### Q3: CUDA out of memory
```bash
RuntimeError: CUDA out of memory

# 解决方案:
python Main.py --batch_size 16  # 减小批次大小
# 或
python Main.py --device cpu     # 使用CPU
```

### Q4: 添加新数据集
```python
# 编辑 dataset_manager.py
DATASETS['MY_DATASET'] = {
    'name': 'MY_DATASET',
    'full_name': 'My Custom Dataset',
    'description': '100只股票 + 新闻',
    'stocks': 100,
    'date_range': {
        'start': '2020-01-01',
        'end': '2023-12-31',
        # ... 其他日期
    },
    'paths': {
        'data_root': 'data/my_dataset',
        'price': 'data/my_dataset/price/preprocessed',
        'text': 'data/my_dataset/text/preprocessed',
        'config': 'config_my_dataset.yml'
    },
    'format': {
        'price': 'tsv',
        'text': 'json_per_day'
    },
    'available': True
}
```

---

## 📊 日志说明

### 训练日志示例
```
================================================================================
🚀 PyTorch Stock Prediction - Multi-Dataset System
================================================================================
🎲 Random seed: 42
================================================================================
📊 数据集配置
================================================================================
数据集: ACL 2018 Stock Prediction Dataset
描述: 88只美股 (2014-2016) + Twitter推文
股票数: 88
时间范围: 2014-01-01 ~ 2016-01-01
✅ 数据集就绪 (88 价格文件, 88 文本目录)
================================================================================
🔧 设备配置
================================================================================
🚀 Using GPU: NVIDIA GeForce RTX 3090
   Memory: 24.0 GB
================================================================================
🔗 因果图配置
================================================================================
因果发现方法: granger
✅ Causal graph loaded from causal_graph.npy
   Shape: (31, 31)
   Method: granger
   Sparsity: 0.200
================================================================================
🤖 模型配置
================================================================================
Model: StockPrediction_VAE_GRU
Total parameters: 2,170,000
Trainable parameters: 2,170,000
Causal graph shape: torch.Size([31, 31])
Causal variables dimension: 64
================================================================================
⚙️  执行器配置
================================================================================
模式: train
批次大小: 32
学习率: 0.001
训练轮数: 15
================================================================================
🎓 开始训练
================================================================================
[训练过程...]
✅ 训练完成!
================================================================================
🎉 程序执行完成
================================================================================
```

---

## 🔗 相关文档

- [PHASE2_MULTI_DATASET_SYSTEM.md](./PHASE2_MULTI_DATASET_SYSTEM.md) - 详细实现报告
- [MULTI_DATASET_FEASIBILITY.md](./MULTI_DATASET_FEASIBILITY.md) - 可行性分析
- [INNOVATION_ALGORITHMS_REPORT.md](./INNOVATION_ALGORITHMS_REPORT.md) - 算法验证
- [CIKM18_DATASET_SETUP_SUCCESS.md](./CIKM18_DATASET_SETUP_SUCCESS.md) - 数据准备

---

## 📞 获取帮助

```bash
# 查看完整帮助
python Main.py --help

# 查看数据集信息
python dataset_manager.py

# 验证系统状态
python verify_innovation_algorithms.py
```

---

**Last Updated**: 2025-01-05  
**Version**: 2.0.0  
**Maintainer**: GitHub Copilot
