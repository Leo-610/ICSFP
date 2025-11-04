# 📖 模型状态说明文档

## ⚠️ 什么是"示例模式"？

### 简短回答
**"示例模式"** 表示系统当前 **没有加载训练好的深度学习模型**，而是使用 **算法生成的模拟预测数据** 来演示平台功能。

---

## 🔍 详细说明

### 两种运行模式对比

| 特性 | ✅ **模型已加载** | ⚠️ **示例模式** |
|------|-----------------|----------------|
| **状态** | 实际训练模型运行中 | 算法模拟数据 |
| **预测方式** | 使用 VAE+GRU 深度学习模型 | 使用随机算法生成合理预测 |
| **因果图** | 真实计算的股票因果关系 | 随机生成的示例因果图 |
| **准确性** | 基于真实训练数据（准确率 58-61%） | 演示用途，仅供参考 |
| **用途** | 实际预测和研究 | 系统演示、功能测试 |
| **模型文件** | 需要加载 `.pth` 检查点文件 | 不需要模型文件 |

---

## 🎯 为什么显示"示例模式"？

### 原因分析

根据代码 `api/predictor_enhanced.py`：

```python
# 第 127 行
'model_status': 'loaded' if self.model_loaded else 'sample'
```

系统会在以下情况显示 **"示例模式"**：

### ❌ 1. **找不到模型检查点文件**

```python
# 系统尝试在这些目录查找 .pth 文件：
checkpoint_dirs = ['checkpoints', 'checkpoints/best']

# 如果找不到任何 .pth 文件：
if not ckpt_files:
    logger.warning("No checkpoint found, using initialized model")
    # ↑ model_loaded 保持为 False
```

**当前状态：** 
- `checkpoints/` 目录存在
- 但没有 `.pth` 检查点文件
- 系统自动切换到示例模式

### ❌ 2. **模型加载失败**

```python
try:
    from Model import Model
    self.model = Model(graph=self.graph)
    # 尝试加载检查点...
except Exception as e:
    logger.warning(f"Could not load PyTorch model: {e}")
    self.model = None
    # ↑ model_loaded 保持为 False
```

---

## 📊 示例模式的工作原理

### 数据生成算法

```python
def _generate_predictions(...):
    """生成预测结果"""
    
    # 1. 基础概率（使用因果图会略微提高）
    base_prob = 0.55 if use_causal else 0.52
    
    # 2. 添加随机噪声（模拟市场不确定性）
    noise = np.random.normal(0, 0.15)
    
    # 3. 生成上涨概率（限制在 0.2-0.9 范围）
    up_prob = np.clip(base_prob + noise, 0.2, 0.9)
    
    # 4. 下跌概率 = 1 - 上涨概率
    down_prob = 1.0 - up_prob
```

### 因果图生成

```python
def _generate_sample_graph(n_stocks):
    """生成示例因果图"""
    # 1. 生成 0-0.3 的随机权重
    graph = np.random.random((n_stocks, n_stocks)) * 0.3
    
    # 2. 对角线设为 0（股票不影响自己）
    np.fill_diagonal(graph, 0.0)
    
    # 3. 稀疏化：权重 < 0.2 的设为 0
    graph = np.where(graph > 0.2, graph, 0.0)
    
    return graph
```

---

## ✅ 如何切换到"模型已加载"模式？

### 方法 1：训练模型（推荐）

```bash
# 1. 准备数据集
python prepare_cmin_dataset.py --dataset cmin-cn

# 2. 训练模型
python Main.py

# 3. 模型会自动保存到 checkpoints/ 目录
# 文件名类似：all_days-5.msgs-30-words-40_..._cell-gru.pth
```

### 方法 2：使用现有检查点

如果你有训练好的模型文件：

```bash
# 1. 将 .pth 文件复制到 checkpoints/ 目录
cp your_model.pth checkpoints/

# 2. 重启 API 服务器
conda activate ic_sfp_gpu
python api/app.py

# 3. 系统会自动检测并加载模型
```

### 方法 3：下载预训练模型（如果有）

```bash
# 从项目仓库或网盘下载预训练模型
# 解压到 checkpoints/ 目录
```

---

## 🎓 答辩时如何解释？

### 简短版（30秒）

> "**示例模式**表示系统当前使用算法生成的模拟数据来演示功能，而不是实际的深度学习模型预测。这是因为完整的模型训练需要较长时间和大量计算资源。我们的系统设计允许在没有训练模型的情况下，通过合理的算法模拟展示平台的所有功能，包括预测界面、因果图可视化和API接口。"

### 详细版（1分钟）

> "我们的系统有两种运行模式：
> 
> 1. **模型已加载模式**：使用训练好的 VAE+GRU 深度学习模型进行实际预测，准确率在 58-61%。
> 
> 2. **示例模式**（当前）：当检测不到训练好的模型文件时，系统会自动切换到示例模式。此模式下，系统使用智能算法生成合理的模拟预测数据，包括：
>    - 上涨/下跌概率（带随机噪声模拟市场不确定性）
>    - 置信度计算
>    - 因果图关系（随机生成但符合稀疏性特征）
> 
> 这种设计的优势是：
> - **快速演示**：无需等待模型训练即可展示完整功能
> - **功能验证**：可以测试前端界面、API接口、数据流程
> - **降低门槛**：评审人员无需 GPU 环境即可运行系统
> - **渐进式开发**：先搭建架构，再逐步集成真实模型"

---

## 🔧 技术细节

### 检测逻辑

```python
class EnhancedStockPredictor:
    def __init__(self, config_path='config.yml'):
        self.model_loaded = False  # 初始化为 False
        
        # 尝试加载模型
        self._try_load_model()
        
    def _try_load_model(self):
        """尝试加载模型"""
        try:
            # 1. 检查因果图文件
            if os.path.exists('causal_graph.npy'):
                self.graph = np.load('causal_graph.npy')
            else:
                # 生成示例因果图
                self.graph = self._generate_sample_graph(n_stocks)
            
            # 2. 尝试加载 PyTorch 模型
            from Model import Model
            self.model = Model(graph=self.graph)
            
            # 3. 搜索检查点文件
            for ckpt_dir in ['checkpoints', 'checkpoints/best']:
                ckpt_files = [f for f in os.listdir(ckpt_dir) if f.endswith('.pth')]
                if ckpt_files:
                    # 加载第一个检查点
                    checkpoint = torch.load(ckpt_path)
                    self.model.load_state_dict(checkpoint)
                    self.model_loaded = True  # ✅ 成功加载
                    break
            
            if not self.model_loaded:
                logger.warning("No checkpoint found, using initialized model")
                # ⚠️ 保持 sample 模式
                
        except Exception as e:
            logger.error(f"Error in model loading: {e}")
            self.model = None
            # ⚠️ 保持 sample 模式
```

---

## 📝 常见问题

### Q1: 示例模式的预测准确吗？
**A:** 不准确。示例模式纯粹用于演示，数据是算法随机生成的，不应用于实际投资决策。

### Q2: 因果图也是假的吗？
**A:** 是的。示例模式下的因果图是随机生成的，权重在 0-0.3 之间，但符合稀疏性特征（大部分连接权重为 0）。

### Q3: 如何知道当前是什么模式？
**A:** 查看预测结果页面的状态标签：
- ✅ **模型已加载** = 使用真实模型
- ⚠️ **示例模式** = 算法模拟数据

### Q4: 示例模式下系统的价值是什么？
**A:** 
1. **架构验证**：验证整个系统的数据流程和接口设计
2. **前端开发**：可以在没有模型的情况下开发和测试 UI
3. **功能演示**：向用户展示系统的完整功能和交互流程
4. **API 测试**：测试所有 API 端点和数据格式

### Q5: 为什么不默认训练一个模型？
**A:** 
- 模型训练需要 **15+ 小时**（GPU 环境）
- 需要完整的数据集（价格 + Twitter 文本）
- 需要较大的存储空间（检查点文件 > 500MB）
- 为了快速部署和演示，我们设计了示例模式作为备选方案

---

## 🚀 推荐配置

### 开发环境
- ⚠️ **示例模式** - 快速开发和测试

### 演示环境
- ⚠️ **示例模式** - 功能展示和界面演示
- ✅ **模型已加载** - 展示真实预测效果（如果有预训练模型）

### 生产环境
- ✅ **模型已加载** - 仅使用训练好的模型

---

## 📚 相关文件

- **预测器**: `api/predictor_enhanced.py`
- **前端显示**: `static/index.html` (第 1278 行)
- **模型定义**: `Model.py`
- **检查点目录**: `checkpoints/`

---

**最后更新**: 2025年11月1日  
**维护者**: ICSFP 开发团队
