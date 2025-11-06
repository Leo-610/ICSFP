# 实时预测路由修复

## 🐛 问题描述

### 错误信息
```
实时预测失败
HTTP 500: INTERNAL SERVER ERROR
```

### 服务器日志
```
2025-11-05 17:31:04 - api.middleware - ERROR - Error handling request: 405 Method Not Allowed: 
The method is not allowed for the requested URL.

werkzeug.exceptions.MethodNotAllowed: 405 Method Not Allowed: 
The method is not allowed for the requested URL.

POST /api/v1/realtime/predict/horizon HTTP/1.1" 500
```

### 根本原因

**路由定义不匹配**：
- **前端调用**：`POST /api/v1/realtime/predict/horizon`（带JSON body）
- **后端路由**：`GET /api/v1/realtime/predict/horizon/<symbol>`（URL参数）

前端代码在 `index.html` 中使用POST方法：
```javascript
const response = await fetch('http://localhost:5000/api/v1/realtime/predict/horizon', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        symbol: stock,
        days: predictionDays,
        use_causal: useCausal
    })
});
```

但 `api/realtime_routes.py` 中只定义了GET方法的路由：
```python
@realtime_bp.route('/predict/horizon/<symbol>', methods=['GET'])
def predict_horizon(symbol: str):
    # GET方法，symbol从URL路径获取，其他参数从query string获取
```

## ✅ 解决方案

### 修改内容

在 `api/realtime_routes.py` 中添加了支持POST方法的新路由：

```python
@realtime_bp.route('/predict/horizon', methods=['POST'])
def predict_horizon_post():
    """
    预测未来多天走势（POST方法）
    
    POST /api/v1/realtime/predict/horizon
    
    Request Body:
    {
        "symbol": "AAPL",
        "days": 5,
        "use_causal": true
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "symbol": "AAPL",
            "current_price": 150.25,
            "horizon_days": 5,
            "predictions": [...],
            "confidence_analysis": {...}
        }
    }
    """
    try:
        from api.realtime_predictor import get_realtime_predictor
        
        data = request.get_json()
        
        if not data or 'symbol' not in data:
            return jsonify({
                'status': 'error',
                'message': 'symbol field is required'
            }), 400
        
        symbol = data['symbol']
        horizon_days = int(data.get('days', 5))
        use_causal = data.get('use_causal', True)
        
        if horizon_days < 1 or horizon_days > 30:
            return jsonify({
                'status': 'error',
                'message': 'days must be between 1 and 30'
            }), 400
        
        predictor = get_realtime_predictor()
        result = predictor.predict_with_horizon(symbol, horizon_days, use_causal)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"Error in horizon prediction for {symbol}: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

### 保留原有GET路由

原有的GET方法路由保持不变，支持RESTful风格的调用：

```python
@realtime_bp.route('/predict/horizon/<symbol>', methods=['GET'])
def predict_horizon(symbol: str):
    """
    预测未来多天走势（GET方法）
    
    GET /api/v1/realtime/predict/horizon/AAPL?days=5&use_causal=true
    """
    # 原有代码保持不变
```

### 两种调用方式

现在支持两种API调用方式：

#### 方式1：POST（推荐，用于前端表单）
```javascript
fetch('/api/v1/realtime/predict/horizon', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        symbol: 'AAPL',
        days: 5,
        use_causal: true
    })
});
```

#### 方式2：GET（用于简单查询）
```javascript
fetch('/api/v1/realtime/predict/horizon/AAPL?days=5&use_causal=true');
```

## 🔧 技术细节

### 路由注册

两个路由函数现在并存：

| 路由 | 方法 | 函数名 | 参数来源 |
|------|------|--------|---------|
| `/predict/horizon/<symbol>` | GET | `predict_horizon()` | URL路径 + Query String |
| `/predict/horizon` | POST | `predict_horizon_post()` | JSON Body |

### 参数验证

两个路由都包含相同的验证逻辑：
- ✅ symbol字段必填
- ✅ days范围：1-30
- ✅ use_causal默认为true

### 错误处理

统一的错误处理机制：
- 400：请求参数错误
- 500：服务器内部错误
- 详细的错误日志记录

## 📊 测试结果

### 修复前
```
POST /api/v1/realtime/predict/horizon
Response: 405 Method Not Allowed
Error: The method is not allowed for the requested URL.
```

### 修复后
```
POST /api/v1/realtime/predict/horizon
Response: 200 OK
Data: {
    "status": "success",
    "data": {
        "symbol": "AAPL",
        "current_price": 178.45,
        "predictions": [...],
        "confidence_analysis": {...}
    }
}
```

## 🚀 部署状态

### 服务器重启
```
✅ API routes registered successfully
✅ Trading routes registered successfully
✅ Realtime data routes registered successfully
✅ SocketIO initialized for realtime data
🌐 Running on http://127.0.0.1:5000
```

### 路由验证

新路由已成功注册：
```python
POST /api/v1/realtime/predict/horizon → predict_horizon_post()
GET  /api/v1/realtime/predict/horizon/<symbol> → predict_horizon()
```

## 📝 相关文件

### 修改的文件
- `d:\ICSFP\HCSF\api\realtime_routes.py`
  - 新增 `predict_horizon_post()` 函数
  - 保留 `predict_horizon()` 函数

### 影响的页面
- `d:\ICSFP\HCSF\static\index.html`
  - 实时预测表单调用此API
  - 前端代码无需修改

## 🎯 最佳实践建议

### API设计原则

1. **RESTful设计**
   - GET：查询操作，参数在URL
   - POST：创建/复杂操作，参数在Body

2. **向后兼容**
   - 保留原有GET路由
   - 新增POST路由
   - 两种方式共存

3. **参数传递**
   - 简单查询：GET + Query String
   - 复杂请求：POST + JSON Body
   - 前端表单：POST（更安全，支持更多数据）

### 前端调用建议

**推荐使用POST方法**：
- ✅ 更安全（数据在Body中）
- ✅ 支持复杂数据结构
- ✅ 更符合RESTful规范
- ✅ 更易于维护和扩展

## 🔍 故障排查步骤

### 如何诊断类似问题

1. **查看浏览器控制台**
   ```
   Failed to fetch
   HTTP 500 Internal Server Error
   ```

2. **查看服务器日志**
   ```
   405 Method Not Allowed
   werkzeug.exceptions.MethodNotAllowed
   ```

3. **对比前后端**
   - 前端调用方法：POST/GET
   - 后端路由定义：methods=['POST', 'GET']
   - URL匹配：路径参数 vs Body参数

4. **测试路由**
   ```bash
   # 测试POST
   curl -X POST http://localhost:5000/api/v1/realtime/predict/horizon \
     -H "Content-Type: application/json" \
     -d '{"symbol":"AAPL","days":5,"use_causal":true}'
   
   # 测试GET
   curl http://localhost:5000/api/v1/realtime/predict/horizon/AAPL?days=5
   ```

## ✅ 验证清单

- [x] 添加POST路由支持
- [x] 保留GET路由兼容性
- [x] 参数验证逻辑一致
- [x] 错误处理完善
- [x] 服务器成功重启
- [x] 日志记录正常
- [x] 前端调用测试通过

## 🎉 修复完成

实时预测功能现在可以正常工作了！用户可以：

1. 访问主页 http://127.0.0.1:5000/
2. 选择"实时数据"作为数据源
3. 选择股票和预测天数
4. 点击"开始预测"
5. 查看实时预测结果和置信度分析

**立即体验修复后的实时预测功能！** 🚀
