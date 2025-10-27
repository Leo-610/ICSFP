# iCast API 使用指南

## 快速开始

### 1. 启动API服务

```bash
# 方法1：直接运行
python api/app.py

# 方法2：使用gunicorn（生产环境）
gunicorn -w 4 -b 0.0.0.0:5000 api.app:create_app()
```

服务启动后，访问 `http://localhost:5000/health` 检查健康状态。

---

## API端点

### 基础信息

- **基础URL**: `http://localhost:5000/api/v1`
- **内容类型**: `application/json`
- **字符编码**: `UTF-8`

---

## 预测接口

### 1. 单股票预测

**端点**: `POST /predict/single`

**描述**: 预测单只股票的涨跌方向

**请求示例**:

```bash
curl -X POST http://localhost:5000/api/v1/predict/single \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "start_date": "2015-10-01",
    "end_date": "2015-10-05",
    "use_causal": true
  }'
```

**Python示例**:

```python
import requests

url = "http://localhost:5000/api/v1/predict/single"
data = {
    "stock_symbol": "AAPL",
    "start_date": "2015-10-01",
    "end_date": "2015-10-05",
    "use_causal": True
}

response = requests.post(url, json=data)
result = response.json()

print(f"Status: {result['status']}")
for pred in result['data']['predictions']:
    print(f"Date: {pred['date']}, Direction: {pred['predicted_direction']}, Confidence: {pred['confidence']:.2%}")
```

**响应**:

```json
{
  "status": "success",
  "data": {
    "stock_symbol": "AAPL",
    "predictions": [
      {
        "date": "2015-10-01",
        "predicted_direction": "UP",
        "confidence": 0.85,
        "probabilities": {
          "UP": 0.85,
          "DOWN": 0.15
        },
        "use_causal": true
      }
    ],
    "model": "all_days-5.msgs-30-words-40_..."
  }
}
```

---

### 2. 批量预测

**端点**: `POST /predict/batch`

**描述**: 批量预测多只股票

**请求示例**:

```python
import requests

url = "http://localhost:5000/api/v1/predict/batch"
data = {
    "stock_symbols": ["AAPL", "GOOG", "MSFT"],
    "start_date": "2015-10-01",
    "end_date": "2015-10-05",
    "use_causal": True
}

response = requests.post(url, json=data)
result = response.json()

print(f"Total stocks: {result['data']['summary']['total_stocks']}")
print(f"Average confidence: {result['data']['summary']['avg_confidence']:.2%}")

for stock, predictions in result['data']['predictions'].items():
    print(f"\n{stock}:")
    for pred in predictions:
        print(f"  {pred['date']}: {pred['predicted_direction']} ({pred['confidence']:.2%})")
```

**响应**:

```json
{
  "status": "success",
  "data": {
    "predictions": {
      "AAPL": [...],
      "GOOG": [...],
      "MSFT": [...]
    },
    "summary": {
      "total_stocks": 3,
      "total_predictions": 15,
      "avg_confidence": 0.78
    }
  }
}
```

---

## 因果分析接口

### 3. 获取因果图

**端点**: `GET /causal/graph`

**描述**: 获取股票间的因果关系图

**请求参数**:
- `stocks` (可选): 逗号分隔的股票代码，如 `AAPL,GOOG,MSFT`
- `threshold` (可选): 因果关系阈值，默认 `0.3`

**请求示例**:

```python
import requests
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

url = "http://localhost:5000/api/v1/causal/graph"
params = {
    "stocks": "AAPL,GOOG,MSFT,FB,ORCL",
    "threshold": 0.3
}

response = requests.get(url, params=params)
result = response.json()

# 可视化因果图
graph = np.array(result['data']['graph'])
stocks = result['data']['stocks']

plt.figure(figsize=(10, 8))
sns.heatmap(graph, xticklabels=stocks, yticklabels=stocks, 
            cmap='YlOrRd', annot=True, fmt='.2f')
plt.title('Causal Relationships')
plt.xlabel('To Stock')
plt.ylabel('From Stock')
plt.tight_layout()
plt.savefig('causal_graph.png')
```

**响应**:

```json
{
  "status": "success",
  "data": {
    "graph": [[0.0, 0.5, 0.3], [0.2, 0.0, 0.4], ...],
    "stocks": ["AAPL", "GOOG", "MSFT"],
    "edges": [
      {"from": "AAPL", "to": "GOOG", "weight": 0.5},
      {"from": "AAPL", "to": "MSFT", "weight": 0.3},
      {"from": "GOOG", "to": "MSFT", "weight": 0.4}
    ],
    "threshold": 0.3
  }
}
```

---

### 4. 因果影响力分析

**端点**: `GET /causal/influence`

**描述**: 分析某只股票的因果影响力

**请求参数**:
- `stock` (必需): 股票代码
- `top_k` (可选): 返回前k个影响最大的股票，默认 `10`

**请求示例**:

```python
import requests

url = "http://localhost:5000/api/v1/causal/influence"
params = {
    "stock": "AAPL",
    "top_k": 5
}

response = requests.get(url, params=params)
result = response.json()

print(f"Causal influence analysis for {result['data']['stock']}:\n")

print("Influenced by:")
for item in result['data']['influenced_by']:
    print(f"  {item['stock']}: {item['weight']:.3f}")

print("\nInfluences:")
for item in result['data']['influences']:
    print(f"  {item['stock']}: {item['weight']:.3f}")
```

**响应**:

```json
{
  "status": "success",
  "data": {
    "stock": "AAPL",
    "influenced_by": [
      {"stock": "GOOG", "weight": 0.8},
      {"stock": "MSFT", "weight": 0.6}
    ],
    "influences": [
      {"stock": "TSLA", "weight": 0.7},
      {"stock": "NVDA", "weight": 0.5}
    ]
  }
}
```

---

## 信息查询接口

### 5. 获取可用股票

**端点**: `GET /stocks`

**描述**: 获取系统中可用的股票列表

**请求参数**:
- `sector` (可选): 板块过滤，如 `tech`, `finance`, `healthcare`

**请求示例**:

```python
import requests

# 获取所有股票
url = "http://localhost:5000/api/v1/stocks"
response = requests.get(url)
result = response.json()

print(f"Total stocks: {len(result['data']['stocks'])}")
print(f"Sectors: {list(result['data']['sectors'].keys())}")

# 获取科技板块股票
response = requests.get(url, params={"sector": "tech"})
result = response.json()
print(f"Tech stocks: {result['data']['stocks']}")
```

**响应**:

```json
{
  "status": "success",
  "data": {
    "stocks": ["AAPL", "GOOG", "MSFT", "JPM", "BAC", ...],
    "sectors": {
      "tech": ["AAPL", "GOOG", "MSFT", "FB", "ORCL"],
      "finance": ["JPM", "BAC", "WFC", "C", "V"],
      "healthcare": ["JNJ", "PFE", "UNH", "MRK", "AMGN"]
    }
  }
}
```

---

### 6. 获取模型信息

**端点**: `GET /model/info`

**描述**: 获取当前加载的模型信息

**请求示例**:

```python
import requests

url = "http://localhost:5000/api/v1/model/info"
response = requests.get(url)
result = response.json()

info = result['data']
print(f"Model: {info['model_name']}")
print(f"Total parameters: {info['total_parameters']:,}")
print(f"Device: {info['device']}")
print(f"Causal graph shape: {info['causal_graph_shape']}")
```

**响应**:

```json
{
  "status": "success",
  "data": {
    "model_name": "all_days-5.msgs-30-words-40_...",
    "total_parameters": 1234567,
    "trainable_parameters": 1234567,
    "device": "cuda",
    "causal_graph_shape": [90, 90],
    "config": {
      "max_n_days": 5,
      "max_n_msgs": 30
    }
  }
}
```

---

## 错误处理

所有错误响应遵循统一格式：

```json
{
  "status": "error",
  "message": "Error description",
  "type": "ValueError"
}
```

**常见错误码**:

- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

**示例**:

```python
response = requests.post(url, json=invalid_data)
if response.status_code != 200:
    error = response.json()
    print(f"Error ({response.status_code}): {error['message']}")
```

---

## 性能优化建议

1. **批量请求**: 使用 `/predict/batch` 而非多次调用 `/predict/single`
2. **缓存**: 对于相同参数的因果图查询，考虑客户端缓存
3. **并发**: API支持并发请求，可使用线程池加速

**并发示例**:

```python
from concurrent.futures import ThreadPoolExecutor
import requests

def predict_stock(symbol):
    url = "http://localhost:5000/api/v1/predict/single"
    data = {"stock_symbol": symbol, "use_causal": True}
    return requests.post(url, json=data).json()

stocks = ["AAPL", "GOOG", "MSFT", "FB", "ORCL"]

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(predict_stock, stocks))

for result in results:
    print(result['data']['stock_symbol'], result['status'])
```

---

## 部署建议

### 开发环境

```bash
python api/app.py
```

### 生产环境

```bash
# 使用gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 api.app:create_app()

# 使用Docker
docker build -t icast-api .
docker run -p 5000:5000 icast-api

# 使用nginx反向代理
# 参见 nginx.conf 配置示例
```

---

## 更多示例

完整的Python客户端库和更多示例，请参见：
- [examples/api_client.py](examples/api_client.py)
- [examples/batch_prediction.py](examples/batch_prediction.py)
- [examples/causal_analysis.py](examples/causal_analysis.py)

---

**需要帮助？** 请访问 [GitHub Issues](https://github.com/wenrui-jiang/HCSF/issues)
