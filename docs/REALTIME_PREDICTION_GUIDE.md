# 实时预测功能使用指南

## 🎯 功能概述

实时预测功能整合了实时数据获取和预测模型，提供真正的实时股票预测服务。

### 核心特性

✅ **实时数据获取** - 从Yahoo Finance等数据源获取最新报价  
✅ **模型预测** - 使用训练好的深度学习模型进行预测  
✅ **批量处理** - 支持同时预测多只股票  
✅ **多天预测** - 预测未来多个交易日的走势  
✅ **置信度评估** - 提供预测的置信度和概率分布  

---

## 📊 测试结果

从刚才的测试可以看到：

```
[3/4] 测试单只股票实时预测...
  ✓ 预测完成
  股票代码: AAPL
  当前价格: $268.18
  预测方向: DOWN
  置信度: 52.9%
  上涨概率: 47.1%
  下跌概率: 52.9%
  预测方法: model

[4/4] 测试批量实时预测...
  代码       价格         预测       置信度        方法
  --------------------------------------------------------
  AAPL     $268.18    ▼DOWN    52.9     % model
  GOOG     $279.35    ▲UP      59.0     % model
  MSFT     $514.01    ▼DOWN    53.1     % model
```

---

## 🚀 使用方法

### 1. Python 脚本调用

```python
from api.realtime_predictor import get_realtime_predictor

# 初始化预测器
predictor = get_realtime_predictor()

# 单只股票预测
result = predictor.predict_realtime('AAPL', use_causal=True)
print(f"{result['symbol']}: {result['prediction']['direction']}")
print(f"置信度: {result['prediction']['confidence']*100:.1f}%")

# 批量预测
results = predictor.predict_realtime_batch(['AAPL', 'GOOG', 'MSFT'])

# 多天预测
horizon = predictor.predict_with_horizon('AAPL', horizon_days=5)
```

### 2. REST API 调用

#### 单只股票预测
```bash
curl http://localhost:5000/api/v1/realtime/predict/AAPL?use_causal=true
```

响应示例：
```json
{
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "timestamp": "2025-11-04T23:58:20",
    "current_price": 268.18,
    "prediction": {
      "direction": "DOWN",
      "confidence": 0.529,
      "probabilities": {
        "UP": 0.471,
        "DOWN": 0.529
      },
      "method": "model"
    },
    "market_data": {
      "open": 268.24,
      "high": 269.59,
      "low": 267.62,
      "volume": 25000000,
      "change_percent": -0.25
    }
  }
}
```

#### 批量预测
```bash
curl -X POST http://localhost:5000/api/v1/realtime/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "GOOG", "MSFT"],
    "use_causal": true
  }'
```

#### 多天预测
```bash
curl "http://localhost:5000/api/v1/realtime/predict/horizon/AAPL?days=5&use_causal=true"
```

响应示例：
```json
{
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "current_price": 268.18,
    "horizon_days": 5,
    "predictions": [
      {
        "date": "2025-11-05",
        "day_offset": 1,
        "predicted_direction": "DOWN",
        "confidence": 0.529
      },
      {
        "date": "2025-11-06",
        "day_offset": 2,
        "predicted_direction": "DOWN",
        "confidence": 0.502
      }
    ]
  }
}
```

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────┐
│            前端/客户端                            │
│    (浏览器、移动应用、Python脚本)                  │
└────────────────┬────────────────────────────────┘
                 │ HTTP REST API
                 ▼
┌─────────────────────────────────────────────────┐
│         API 路由层 (realtime_routes.py)          │
│  ┌──────────────────────────────────────────┐  │
│  │ /realtime/predict/<symbol>                │  │
│  │ /realtime/predict/batch                   │  │
│  │ /realtime/predict/horizon/<symbol>        │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│    实时预测器 (RealtimePredictor)                │
│  ┌──────────────────┐  ┌────────────────────┐  │
│  │  数据管理器       │  │   预测模型          │  │
│  │ (RealtimeData    │  │ (EnhancedStock     │  │
│  │  Manager)        │  │  Predictor)        │  │
│  └──────────────────┘  └────────────────────┘  │
│                                                 │
│  工作流程:                                       │
│  1. 获取实时报价                                 │
│  2. 获取历史数据                                 │
│  3. 特征工程                                    │
│  4. 模型推理                                    │
│  5. 结果整合                                    │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐   ┌────────────────┐
│ 数据源层      │   │  预测模型       │
│ Yahoo Finance│   │  PyTorch模型    │
│ Alpha Vantage│   │  因果图增强     │
│ Tushare      │   │  特征提取       │
└──────────────┘   └────────────────┘
```

---

## 📝 API 端点

### 实时数据相关
- `GET /api/v1/realtime/quote/<symbol>` - 获取实时报价
- `POST /api/v1/realtime/quotes` - 批量获取报价
- `GET /api/v1/realtime/historical/<symbol>` - 获取历史数据
- `GET /api/v1/realtime/market/summary` - 市场摘要

### 实时预测相关
- `GET /api/v1/realtime/predict/<symbol>` - 单只股票预测
- `POST /api/v1/realtime/predict/batch` - 批量预测
- `GET /api/v1/realtime/predict/horizon/<symbol>` - 多天预测

---

## 💡 关键特性说明

### 1. 特征工程

预测器自动从实时和历史数据中提取以下特征：
- 最近收益率 (1天、5天、10天)
- 价格波动率
- 价格趋势
- 成交量变化
- 当前涨跌幅

### 2. 预测方法

支持两种预测方法：
- **model** - 使用训练好的深度学习模型
- **rule-based** - 基于规则的备用预测（模型未加载时）

### 3. 置信度计算

置信度反映模型对预测结果的确信程度：
- **50-60%** - 低置信度，建议谨慎
- **60-75%** - 中等置信度，可参考
- **75%+** - 高置信度，较可靠

### 4. 因果图增强

当 `use_causal=true` 时，预测会考虑股票之间的因果关系，提高预测准确度。

---

## 🎨 前端集成

### 在现有页面中添加实时预测

在 `static/index.html` 或 `static/realtime.html` 中：

```javascript
// 获取实时预测
async function getRealtimePrediction(symbol) {
    const response = await fetch(`/api/v1/realtime/predict/${symbol}`);
    const data = await response.json();
    
    if (data.status === 'success') {
        const pred = data.data;
        console.log(`${pred.symbol}: ${pred.prediction.direction}`);
        console.log(`置信度: ${pred.prediction.confidence * 100}%`);
        
        // 更新UI显示预测结果
        updatePredictionUI(pred);
    }
}

// 批量预测
async function getBatchPredictions(symbols) {
    const response = await fetch('/api/v1/realtime/predict/batch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({symbols, use_causal: true})
    });
    
    const data = await response.json();
    return data.data;
}
```

---

## 📈 性能指标

基于测试结果：

- **响应时间**: 2-3秒（包括数据获取和模型推理）
- **准确率**: 取决于模型训练效果和市场条件
- **并发能力**: 支持多用户同时请求
- **数据新鲜度**: 实时数据，缓存TTL可配置（默认60秒）

---

## 🔧 配置选项

在 `config/realtime_config.yml` 中可以配置：

```yaml
# 缓存设置（影响数据新鲜度）
cache:
  ttl: 60  # 秒

# 数据源优先级
data_sources:
  yahoo_finance:
    enabled: true
    priority: 1

# 预测参数
prediction:
  default_horizon_days: 5
  max_horizon_days: 30
  confidence_threshold: 0.6
```

---

## ⚠️ 注意事项

1. **免责声明**: 预测结果仅供参考，不构成投资建议
2. **数据延迟**: 实时数据可能有15-20分钟延迟（取决于数据源）
3. **API限制**: 注意数据源的API调用频率限制
4. **模型限制**: 预测准确度受市场波动和模型训练质量影响

---

## 🔍 故障排查

### 问题1: 预测失败
```python
# 检查数据是否获取成功
from api.realtime_data import get_realtime_manager
manager = get_realtime_manager()
quote = manager.get_realtime_quote('AAPL')
print(quote)
```

### 问题2: 模型未加载
```python
# 检查模型状态
from api.predictor_enhanced import EnhancedStockPredictor
predictor = EnhancedStockPredictor()
print(f"Model loaded: {predictor.model_loaded}")
```

### 问题3: 数据源错误
- 检查网络连接
- 验证API密钥（如使用Alpha Vantage或Tushare）
- 查看日志文件

---

## 📚 相关文档

- [实时数据模块文档](REALTIME_DATA_MODULE.md)
- [API完整文档](../docs/API_GUIDE.md)
- [配置说明](../config/realtime_config.yml)

---

## 🎉 下一步计划

- [ ] 添加数据可视化（K线图、趋势图）
- [ ] 实现价格告警功能
- [ ] 优化缓存策略
- [ ] 添加数据持久化
- [ ] 扩展更多预测指标

---

## 📧 支持

如有问题或建议，请查看项目文档或联系开发团队。
