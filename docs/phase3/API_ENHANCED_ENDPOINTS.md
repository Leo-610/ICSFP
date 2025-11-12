# Phase 3 增强 API 端点文档

本文档介绍了 ICSFP Phase 3 新增的增强 API 端点，用于集成性能优化、CUTS+ 因果发现和统一管道功能。

## 📋 目录

- [概述](#概述)
- [认证](#认证)
- [性能优化端点](#性能优化端点)
- [CUTS+ 因果发现端点](#cuts-因果发现端点)
- [统一管道端点](#统一管道端点)
- [系统监控端点](#系统监控端点)
- [错误处理](#错误处理)
- [示例代码](#示例代码)

---

## 概述

**基础 URL**: `http://localhost:5000/api/v1/enhanced`

**返回格式**: JSON

**字符编码**: UTF-8

**新增端点数量**: 10 个

### 功能分类

1. **性能优化** (3 端点): GPU 加速、缓存管理
2. **CUTS+ 因果发现** (2 端点): 自适应因果发现方法
3. **统一管道** (2 端点): 端到端工作流执行
4. **系统监控** (3 端点): 系统状态与健康检查

---

## 认证

当前版本所有端点均为公开访问,未来版本将支持 API Key 认证。

---

## 性能优化端点

### 1. GPU 加速因果发现

**端点**: `POST /api/v1/enhanced/performance/optimize_causal`

**描述**: 使用 GPU 加速执行因果发现,支持批处理和智能缓存。

**请求体**:
```json
{
  "stock_codes": ["000001.SZ", "600000.SH"],
  "method": "granger",
  "use_gpu": true,
  "cache_enabled": true,
  "batch_size": 16
}
```

**参数说明**:
- `stock_codes` (array, required): 股票代码列表
- `method` (string, optional): 因果发现方法 (默认: "granger")
  - 可选值: "granger", "cuts_plus", "correlation"
- `use_gpu` (boolean, optional): 是否使用 GPU (默认: true)
- `cache_enabled` (boolean, optional): 是否启用缓存 (默认: true)
- `batch_size` (integer, optional): 批处理大小 (默认: 16)

**响应示例**:
```json
{
  "success": true,
  "results": {
    "causal_graph": [[0.0, 0.75], [0.0, 0.0]],
    "significant_edges": 1,
    "stock_names": ["平安银行", "浦发银行"]
  },
  "performance": {
    "execution_time": 0.324,
    "gpu_used": true,
    "cache_hit": false,
    "gpu_memory_used_mb": 256.5
  },
  "message": "因果发现完成 (GPU 加速)"
}
```

**性能提升**:
- GPU 加速: 约 3-5x 速度提升
- 缓存命中: 约 3.5x 速度提升
- 批处理优化: 显著减少内存占用

---

### 2. 性能状态查询

**端点**: `GET /api/v1/enhanced/performance/status`

**描述**: 获取系统性能状态,包括 GPU 信息、缓存统计。

**响应示例**:
```json
{
  "success": true,
  "status": {
    "gpu": {
      "available": true,
      "device_name": "NVIDIA GeForce RTX 4060",
      "memory_allocated_mb": 512.3,
      "memory_cached_mb": 1024.6,
      "total_memory_gb": 8.59,
      "utilization_percent": 35.2
    },
    "cache": {
      "enabled": true,
      "size": 128,
      "hits": 245,
      "misses": 67,
      "hit_rate": 0.785,
      "speedup": "3.54x"
    },
    "optimizer": {
      "initialized": true,
      "batch_size": 16,
      "num_workers": 4
    }
  }
}
```

---

### 3. 清除缓存

**端点**: `POST /api/v1/enhanced/performance/cache/clear`

**描述**: 清除所有缓存数据,释放内存。

**请求体**: (可选)
```json
{
  "scope": "all"
}
```

**参数说明**:
- `scope` (string, optional): 清除范围
  - `all`: 清除所有缓存 (默认)
  - `causal`: 仅清除因果发现缓存
  - `prediction`: 仅清除预测缓存

**响应示例**:
```json
{
  "success": true,
  "message": "缓存已清除",
  "details": {
    "cache_size_before": 128,
    "cache_size_after": 0,
    "memory_freed_mb": 245.6
  }
}
```

---

## CUTS+ 因果发现端点

### 4. CUTS+ 因果发现

**端点**: `POST /api/v1/enhanced/causal/cutsplus`

**描述**: 使用 CUTS+ 方法进行自适应因果发现,支持多种阈值策略。

**请求体**:
```json
{
  "stock_codes": ["000001.SZ", "600000.SH", "000002.SZ"],
  "threshold": "adaptive",
  "alpha": 0.05,
  "lag": 5,
  "use_gpu": true
}
```

**参数说明**:
- `stock_codes` (array, required): 股票代码列表 (最少 2 个)
- `threshold` (string/float, optional): 阈值策略 (默认: "adaptive")
  - `"adaptive"`: 自适应阈值 (推荐)
  - `"percentile"`: 百分位数阈值
  - 数值: 固定阈值 (0.0-1.0)
- `alpha` (float, optional): 显著性水平 (默认: 0.05)
- `lag` (integer, optional): 时滞阶数 (默认: 5)
- `use_gpu` (boolean, optional): 是否使用 GPU (默认: true)

**响应示例**:
```json
{
  "success": true,
  "method": "cuts_plus",
  "results": {
    "causal_graph": [[0.0, 0.82, 0.15], [0.0, 0.0, 0.65], [0.0, 0.0, 0.0]],
    "significant_edges": 3,
    "threshold_used": 0.34,
    "stock_names": ["平安银行", "浦发银行", "万科A"]
  },
  "metadata": {
    "execution_time": 0.456,
    "gpu_used": true,
    "threshold_strategy": "adaptive",
    "data_shape": [3, 100]
  }
}
```

**CUTS+ 优势**:
- **自适应阈值**: 根据数据特征自动调整
- **多尺度分析**: 捕捉不同时间尺度的因果关系
- **鲁棒性强**: 对噪声和异常值具有较好的抵抗能力

---

### 5. 获取可用因果方法

**端点**: `GET /api/v1/enhanced/causal/methods`

**描述**: 获取所有可用的因果发现方法及其说明。

**响应示例**:
```json
{
  "success": true,
  "methods": [
    {
      "name": "granger",
      "display_name": "Granger 因果检验",
      "description": "经典时间序列因果分析方法",
      "supports_gpu": true,
      "typical_execution_time": "0.2-0.5s"
    },
    {
      "name": "cuts_plus",
      "display_name": "CUTS+",
      "description": "自适应因果发现方法,支持多尺度分析",
      "supports_gpu": true,
      "typical_execution_time": "0.4-0.8s"
    },
    {
      "name": "correlation",
      "display_name": "相关性分析",
      "description": "基于皮尔逊相关系数的因果推断",
      "supports_gpu": false,
      "typical_execution_time": "0.1-0.2s"
    }
  ],
  "total_methods": 3
}
```

---

## 统一管道端点

### 6. 运行端到端管道

**端点**: `POST /api/v1/enhanced/pipeline/run`

**描述**: 执行完整的端到端工作流,包括数据加载、因果发现、模型预测。

**请求体**:
```json
{
  "stock_codes": ["000001.SZ", "600000.SH"],
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "causal_method": "cuts_plus",
  "prediction_days": 5,
  "use_gpu": true
}
```

**参数说明**:
- `stock_codes` (array, required): 股票代码列表
- `start_date` (string, optional): 开始日期 (YYYY-MM-DD)
- `end_date` (string, optional): 结束日期 (YYYY-MM-DD)
- `causal_method` (string, optional): 因果发现方法 (默认: "cuts_plus")
- `prediction_days` (integer, optional): 预测天数 (默认: 5)
- `use_gpu` (boolean, optional): 是否使用 GPU (默认: true)

**响应示例**:
```json
{
  "success": true,
  "results": {
    "data_loading": {
      "status": "success",
      "num_stocks": 2,
      "date_range": ["2023-01-01", "2023-12-31"],
      "data_points": 244
    },
    "causal_discovery": {
      "status": "success",
      "method": "cuts_plus",
      "significant_edges": 1,
      "execution_time": 0.456
    },
    "prediction": {
      "status": "success",
      "predictions": [
        {"stock": "000001.SZ", "days": [0.023, 0.015, -0.008, 0.012, 0.019]},
        {"stock": "600000.SH", "days": [0.018, 0.021, 0.009, -0.003, 0.011]}
      ],
      "confidence_scores": [0.85, 0.82]
    }
  },
  "performance": {
    "total_time": 1.234,
    "gpu_used": true,
    "cache_hits": 0
  }
}
```

---

### 7. 管道状态查询

**端点**: `GET /api/v1/enhanced/pipeline/status`

**描述**: 获取统一管道各组件的初始化状态。

**响应示例**:
```json
{
  "success": true,
  "pipeline": {
    "initialized": true,
    "components": {
      "data_loader": "ready",
      "causal_discovery": "ready",
      "predictor": "ready"
    },
    "config": {
      "default_causal_method": "cuts_plus",
      "gpu_enabled": true,
      "cache_enabled": true
    }
  }
}
```

---

## 系统监控端点

### 8. 综合系统监控

**端点**: `GET /api/v1/enhanced/monitor/system`

**描述**: 获取完整的系统监控信息,包括 GPU、内存、缓存、CPU 等。

**响应示例**:
```json
{
  "success": true,
  "system": {
    "timestamp": "2024-01-15T10:30:45.123Z",
    "gpu": {
      "available": true,
      "device": "NVIDIA GeForce RTX 4060",
      "memory_used_gb": 0.5,
      "memory_total_gb": 8.59,
      "utilization": 35.2,
      "temperature_celsius": 62
    },
    "memory": {
      "total_gb": 32.0,
      "available_gb": 18.5,
      "percent_used": 42.2
    },
    "cpu": {
      "percent_used": 28.5,
      "cores": 16
    },
    "cache": {
      "size": 128,
      "hit_rate": 0.785,
      "speedup": "3.54x"
    },
    "performance": {
      "optimizer_status": "active",
      "gpu_acceleration": "enabled",
      "batch_processing": "enabled"
    }
  }
}
```

---

## 错误处理

所有端点使用统一的错误响应格式:

```json
{
  "success": false,
  "error": "错误类型",
  "message": "详细错误信息",
  "details": {
    "field": "问题字段",
    "value": "问题值",
    "expected": "期望值"
  }
}
```

### 常见错误代码

| HTTP 状态码 | 错误类型 | 说明 |
|------------|---------|------|
| 400 | Bad Request | 请求参数错误 |
| 404 | Not Found | 资源未找到 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务暂时不可用 (如 GPU 内存不足) |

### 错误示例

**缺少必需参数**:
```json
{
  "success": false,
  "error": "Missing Required Field",
  "message": "缺少必需字段: stock_codes"
}
```

**GPU 内存不足**:
```json
{
  "success": false,
  "error": "GPU Out of Memory",
  "message": "GPU 内存不足,请减少 batch_size 或禁用 GPU",
  "details": {
    "memory_required_mb": 2048,
    "memory_available_mb": 512
  }
}
```

---

## 示例代码

### Python 示例

```python
import requests

# 基础配置
BASE_URL = "http://localhost:5000/api/v1/enhanced"

# 1. GPU 加速因果发现
def gpu_causal_discovery():
    response = requests.post(
        f"{BASE_URL}/performance/optimize_causal",
        json={
            "stock_codes": ["000001.SZ", "600000.SH"],
            "method": "cuts_plus",
            "use_gpu": True,
            "batch_size": 16
        }
    )
    print(response.json())

# 2. 查询性能状态
def check_performance():
    response = requests.get(f"{BASE_URL}/performance/status")
    data = response.json()
    print(f"GPU 可用: {data['status']['gpu']['available']}")
    print(f"缓存命中率: {data['status']['cache']['hit_rate']:.2%}")

# 3. 运行完整管道
def run_full_pipeline():
    response = requests.post(
        f"{BASE_URL}/pipeline/run",
        json={
            "stock_codes": ["000001.SZ", "600000.SH", "000002.SZ"],
            "causal_method": "cuts_plus",
            "prediction_days": 5,
            "use_gpu": True
        }
    )
    results = response.json()
    print(f"预测结果: {results['results']['prediction']}")

# 4. CUTS+ 因果发现
def cuts_plus_analysis():
    response = requests.post(
        f"{BASE_URL}/causal/cutsplus",
        json={
            "stock_codes": ["000001.SZ", "600000.SH", "000002.SZ"],
            "threshold": "adaptive",
            "use_gpu": True
        }
    )
    print(response.json())

if __name__ == "__main__":
    gpu_causal_discovery()
    check_performance()
    run_full_pipeline()
    cuts_plus_analysis()
```

### JavaScript/Fetch 示例

```javascript
const BASE_URL = 'http://localhost:5000/api/v1/enhanced';

// 1. GPU 加速因果发现
async function gpuCausalDiscovery() {
  const response = await fetch(`${BASE_URL}/performance/optimize_causal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      stock_codes: ['000001.SZ', '600000.SH'],
      method: 'cuts_plus',
      use_gpu: true,
      batch_size: 16
    })
  });
  const data = await response.json();
  console.log(data);
}

// 2. 查询性能状态
async function checkPerformance() {
  const response = await fetch(`${BASE_URL}/performance/status`);
  const data = await response.json();
  console.log(`GPU 可用: ${data.status.gpu.available}`);
  console.log(`缓存命中率: ${(data.status.cache.hit_rate * 100).toFixed(2)}%`);
}

// 3. 系统监控
async function systemMonitoring() {
  const response = await fetch(`${BASE_URL}/monitor/system`);
  const data = await response.json();
  console.log('系统状态:', data.system);
}

// 使用示例
gpuCausalDiscovery();
checkPerformance();
systemMonitoring();
```

### cURL 示例

```bash
# 1. GPU 加速因果发现
curl -X POST http://localhost:5000/api/v1/enhanced/performance/optimize_causal \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001.SZ", "600000.SH"],
    "method": "cuts_plus",
    "use_gpu": true,
    "batch_size": 16
  }'

# 2. 查询性能状态
curl http://localhost:5000/api/v1/enhanced/performance/status

# 3. CUTS+ 因果发现
curl -X POST http://localhost:5000/api/v1/enhanced/causal/cutsplus \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001.SZ", "600000.SH", "000002.SZ"],
    "threshold": "adaptive"
  }'

# 4. 运行完整管道
curl -X POST http://localhost:5000/api/v1/enhanced/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001.SZ", "600000.SH"],
    "causal_method": "cuts_plus",
    "prediction_days": 5
  }'

# 5. 系统监控
curl http://localhost:5000/api/v1/enhanced/monitor/system
```

---

## 性能优化建议

### 1. 批处理优化
- 建议 `batch_size` 设置为 8-32 之间
- GPU 内存充足时可增大批量大小

### 2. 缓存策略
- 对重复查询启用缓存 (`cache_enabled: true`)
- 定期清除缓存以释放内存

### 3. GPU 使用
- 小数据集 (< 10 股票) 可考虑禁用 GPU
- 大规模计算时启用 GPU 加速

### 4. 并发控制
- 建议同时运行的请求数 ≤ 4
- 避免同时多个 GPU 密集型请求

---

## 版本历史

- **v1.0.0** (2024-01-15): 初始版本,包含 10 个增强端点
  - 性能优化端点 (3 个)
  - CUTS+ 因果发现端点 (2 个)
  - 统一管道端点 (2 个)
  - 系统监控端点 (3 个)

---

## 联系与支持

- **文档反馈**: 请在项目仓库提交 Issue
- **性能问题**: 查看 [PERFORMANCE_OPTIMIZATION.md](./PERFORMANCE_OPTIMIZATION.md)
- **CUTS+ 详细说明**: 查看 [CUTS_PLUS_INTEGRATION_REPORT.md](./CUTS_PLUS_INTEGRATION_REPORT.md)

---

**最后更新**: 2024-01-15  
**维护者**: ICSFP Development Team
