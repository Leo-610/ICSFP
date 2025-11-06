# 预测机制说明文档

## 📊 当前预测系统工作原理

### 1. 预测流程概述

```
用户请求预测
    ↓
检查模型加载状态
    ↓
┌─────────────┬────────────────┐
│  模型已加载  │   模型未加载    │
└─────────────┴────────────────┘
       ↓                ↓
   深度学习预测      规则预测
       ↓                ↓
   返回预测结果  ← ← ← ←
```

### 2. 模型加载逻辑

#### 2.1 初始化时 (`EnhancedStockPredictor.__init__`)

```python
self.model_loaded = False  # 默认未加载

# 尝试加载流程：
1. 加载因果图 (causal_graph.npy)
2. 初始化模型结构 (Model类)
3. 搜索checkpoint文件：
   - checkpoints/*.pth
   - checkpoints/*/model.pth
   - checkpoints/best/*.pth
4. 加载第一个找到的有效checkpoint
5. 成功则 model_loaded = True
```

#### 2.2 检查点搜索路径

```
checkpoints/
├── *.pth                        # 直接在根目录
├── [子目录]/
│   └── model.pth               # 子目录中的model.pth
└── best/
    └── *.pth                    # best目录中的文件
```

### 3. 两种预测模式

#### 3.1 深度学习预测 (model_loaded = True)

**特点：**
- ✅ 使用训练好的VAE+GRU模型
- ✅ 因果图增强
- ✅ 高置信度预测
- ✅ 推理速度约50ms

**预测依据：**
```python
# 输入特征：
1. 最近1天收益率
2. 最近5天平均收益率
3. 最近10天平均收益率
4. 最近10天波动率
5. 价格趋势(5天)
6. 成交量变化
7. 当前涨跌幅

# 模型推理：
features → VAE编码器 → 隐变量 → GRU → 因果图增强 → 预测结果
```

#### 3.2 规则预测 (model_loaded = False)

**特点：**
- ⚠️ 使用简单规则引擎
- ⚠️ 基于技术指标
- ⚠️ 中等置信度
- ⚠️ 无深度学习

**预测规则：**
```python
if recent_return > 0.01:
    direction = 'UP'
    up_prob = 0.65
    down_prob = 0.35
elif recent_return < -0.01:
    direction = 'DOWN'
    up_prob = 0.35
    down_prob = 0.65
else:
    direction = 'UP'  # 默认看涨
    up_prob = 0.52
    down_prob = 0.48
```

### 4. 预测方法标识

每个预测结果都包含 `method` 字段：

```json
{
    "direction": "UP",
    "confidence": 0.72,
    "probabilities": {
        "UP": 0.72,
        "DOWN": 0.28
    },
    "method": "model"  // 或 "rule-based"
}
```

### 5. 模型状态查询

#### API端点：
```
GET /api/v1/realtime/model/status
```

#### 响应示例：
```json
{
    "status": "success",
    "data": {
        "model_loaded": true,
        "model_type": "VAE + GRU",
        "parameters": "2.17M",
        "causal_enabled": true,
        "training_dataset": "CMIN-CN",
        "device": "cuda",
        "inference_speed": "~50ms",
        "checkpoint_path": "checkpoints/best/model.pth",
        "prediction_method": "deep_learning"
    }
}
```

### 6. 如何确保模型加载

#### 方法1：检查checkpoint文件

```bash
# 检查是否存在模型文件
ls checkpoints/*.pth
ls checkpoints/*/model.pth
ls checkpoints/best/*.pth
```

#### 方法2：查看日志

```python
# 启动时会输出：
INFO - Loaded causal graph: (X, X)
INFO - Successfully loaded checkpoint: checkpoints/xxx/model.pth
INFO - Enhanced predictor initialized on cuda
```

#### 方法3：API查询

```bash
curl http://localhost:5000/api/v1/realtime/model/status
```

### 7. 常见问题

#### Q1: 为什么模型状态显示"未加载"？

**可能原因：**
1. ❌ checkpoints目录不存在或为空
2. ❌ checkpoint文件损坏
3. ❌ Model类定义与checkpoint不匹配
4. ❌ PyTorch版本不兼容

**解决方法：**
```bash
# 1. 检查checkpoint文件
ls -la checkpoints/

# 2. 检查日志错误信息
tail -f logs/app.log | grep -i "checkpoint\|model"

# 3. 手动测试加载
python -c "from api.predictor_enhanced import EnhancedStockPredictor; p = EnhancedStockPredictor(); print(p.model_loaded)"
```

#### Q2: 规则预测的准确率如何？

**说明：**
- 规则预测仅基于简单的技术指标
- 不使用深度学习
- 准确率约50-55%（接近随机）
- **强烈建议加载模型后使用**

#### Q3: 如何切换到模型预测？

**步骤：**
1. 准备训练好的模型checkpoint
2. 放置到以下任一位置：
   - `checkpoints/model.pth`
   - `checkpoints/best/model.pth`
   - `checkpoints/[任意目录]/model.pth`
3. 重启服务
4. 检查日志确认加载成功

### 8. 性能对比

| 特性 | 深度学习模式 | 规则模式 |
|------|-------------|---------|
| 模型加载 | ✅ 必需 | ❌ 不需要 |
| 预测准确率 | 65-75% | 50-55% |
| 置信度 | 高 (0.6-0.9) | 中 (0.5-0.7) |
| 推理速度 | ~50ms | <1ms |
| 因果增强 | ✅ 支持 | ❌ 不支持 |
| GPU加速 | ✅ 支持 | ❌ 不需要 |

### 9. 技术细节

#### 模型架构 (VAE + GRU)

```
输入特征 (7维)
    ↓
VAE编码器
    ↓
隐变量空间 (潜在表示)
    ↓
GRU循环层
    ↓
因果图注意力层
    ↓
全连接层
    ↓
预测输出 (UP/DOWN概率)
```

#### 因果图增强

```python
# 因果图矩阵: [n_stocks × n_stocks]
# 值: 0.0-1.0 表示因果关系强度

stock_i 的预测 = f(
    stock_i_features,
    Σ(causal_weight[j→i] * stock_j_features)
)
```

### 10. 前端集成

#### 动态显示模型状态

```javascript
// 获取模型状态
fetch('/api/v1/realtime/model/status')
    .then(res => res.json())
    .then(data => {
        const status = data.data.model_loaded ? 
            '<span class="status-success">✅ 已加载</span>' :
            '<span class="status-warning">⚠️ 未加载 (使用规则预测)</span>';
        
        document.getElementById('modelStatus').innerHTML = status;
        document.getElementById('predictionMethod').textContent = 
            data.data.prediction_method === 'deep_learning' ? 
            '深度学习' : '规则引擎';
    });
```

---

## 📝 总结

当前系统支持两种预测模式：

1. **深度学习模式**（推荐）
   - 需要加载训练好的模型checkpoint
   - 高准确率和置信度
   - 支持因果图增强

2. **规则模式**（备用）
   - 无需模型文件
   - 基于简单技术指标
   - 准确率较低

**建议：** 尽快加载训练好的模型以获得更好的预测效果。

---

*最后更新：2025-11-05*
