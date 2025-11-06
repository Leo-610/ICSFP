# ICSFP 集成应用使用指南

## 🎯 概述

ICSFP集成应用将原有的模型训练/预测功能与新的实时数据和可视化模块完整集成，提供一站式股票预测解决方案。

## 🚀 快速启动

### 方法1: 使用快速启动脚本（推荐）

```bash
# 激活环境
conda activate ic_sfp_gpu

# 一键启动Web界面
python quickstart_web.py
```

这将：
- ✅ 自动检查环境和依赖
- ✅ 启动Web服务器（端口5000）
- ✅ 自动在浏览器中打开可视化页面
- ✅ 显示所有可用的功能和API端点

### 方法2: 使用集成应用脚本

```bash
# 启动Web界面
python app_integrated.py --web

# 启动Web界面并自动打开浏览器
python app_integrated.py --web --browser

# 交互模式（菜单式操作）
python app_integrated.py --interactive
```

### 方法3: 直接启动API服务器

```bash
# 直接运行API服务器
python api/app.py
```

然后在浏览器中访问：
- http://127.0.0.1:5000/static/advanced_visualization.html

## 📊 可用页面

启动服务器后，可以访问以下页面：

### 1. 高级可视化页面（推荐）
**URL**: http://127.0.0.1:5000/static/advanced_visualization.html

**功能**:
- 📈 多图表展示（价格、成交量、波动率）
- 🎯 多天预测可视化（1-7天）
- 🔌 WebSocket实时数据推送
- 📋 历史数据表格
- 📱 完全响应式设计

**使用步骤**:
1. 输入股票代码（如：AAPL）
2. 选择时间范围（7天/30天/90天）
3. 点击"🔄 刷新全部"加载数据
4. 点击"🎯 多天预测"查看预测结果
5. 点击"🔌 连接WebSocket"启用实时推送

### 2. 基础可视化页面
**URL**: http://127.0.0.1:5000/static/visualization.html

**功能**:
- 📊 价格走势图
- 🎯 单只股票预测
- 💯 置信度可视化
- 📊 市场数据展示
- 🔄 自动刷新功能

**使用步骤**:
1. 输入股票代码
2. 选择历史天数
3. 点击"🔍 加载数据"
4. 点击"🎯 预测"获取预测结果

### 3. 实时监控页面
**URL**: http://127.0.0.1:5000/static/realtime.html

**功能**:
- 🔌 WebSocket实时连接
- 📊 多股票订阅
- ⚡ 实时报价更新
- 📈 市场统计概览

## 🔌 API使用

### 健康检查
```bash
curl http://127.0.0.1:5000/api/v1/health
```

### 获取实时报价
```bash
# 单只股票
curl http://127.0.0.1:5000/api/v1/realtime/quote/AAPL

# 多只股票（POST）
curl -X POST http://127.0.0.1:5000/api/v1/realtime/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOG", "MSFT"]}'
```

### 获取历史数据
```bash
curl "http://127.0.0.1:5000/api/v1/realtime/historical/AAPL?start_date=2024-01-01&end_date=2024-12-31"
```

### 实时预测
```bash
# 单只股票预测
curl "http://127.0.0.1:5000/api/v1/realtime/predict/AAPL?use_causal=true"

# 批量预测（POST）
curl -X POST http://127.0.0.1:5000/api/v1/realtime/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOG", "MSFT"], "use_causal": true}'

# 多天预测
curl "http://127.0.0.1:5000/api/v1/realtime/predict/horizon/AAPL?horizon_days=5&use_causal=true"
```

## 🎮 集成应用命令

### 交互模式
```bash
python app_integrated.py --interactive
```

菜单选项：
1. 启动Web界面（推荐）
2. 训练模型
3. 查看预测结果
4. 实时预测
5. 打开可视化页面
0. 退出

### 命令行模式

#### 启动Web界面
```bash
python app_integrated.py --web
```

#### 训练模型
```bash
python app_integrated.py --train
```

#### 查看预测结果
```bash
# 查看单只股票
python app_integrated.py --predict AAPL
```

#### 实时预测
```bash
# 预测单只股票
python app_integrated.py --realtime AAPL

# 预测多只股票
python app_integrated.py --realtime AAPL,GOOG,MSFT
```

## 🔧 配置说明

### 实时数据配置
配置文件：`config/realtime_config.yml`

```yaml
cache:
  memory_ttl: 60          # 内存缓存过期时间（秒）
  file_ttl: 3600          # 文件缓存过期时间（秒）
  max_memory_size: 100    # 最大内存缓存条目数

data_sources:
  default: yahoo_finance  # 默认数据源
  yahoo_finance:
    enabled: true
    timeout: 10
  alpha_vantage:
    enabled: false
    api_key: "YOUR_API_KEY"
  tushare:
    enabled: false
    token: "YOUR_TOKEN"

websocket:
  max_clients: 100
  update_interval: 5      # WebSocket推送间隔（秒）
```

### 模型配置
配置文件：`config.yml`

主要参数：
- `batch_size`: 批次大小（默认32）
- `learning_rate`: 学习率（默认0.001）
- `dropout`: Dropout率（默认0.3）
- `cell_type`: RNN单元类型（gru/lstm）
- `use_causal`: 是否使用因果图增强

## 📚 完整工作流程

### 1. 首次使用

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 训练模型（可选，如果已有模型则跳过）
python app_integrated.py --train

# 3. 启动Web界面
python quickstart_web.py
```

### 2. 日常使用

```bash
# 直接启动Web界面
python quickstart_web.py
```

### 3. 开发调试

```bash
# 交互模式，方便测试各个功能
python app_integrated.py --interactive
```

## 🎯 使用场景

### 场景1: 实时监控多只股票
1. 启动Web服务器
2. 打开"实时监控"页面
3. 点击"连接WebSocket"
4. 订阅多只股票（AAPL, GOOG, MSFT等）
5. 实时查看价格变化

### 场景2: 深度分析单只股票
1. 启动Web服务器
2. 打开"高级可视化"页面
3. 输入股票代码（如AAPL）
4. 查看价格、成交量、波动率图表
5. 进行5天预测分析

### 场景3: 批量预测
```bash
python app_integrated.py --realtime AAPL,GOOG,MSFT,TSLA,AMZN
```

### 场景4: API集成
在你的应用中调用ICSFP的API：

```python
import requests

# 获取预测
response = requests.get('http://127.0.0.1:5000/api/v1/realtime/predict/AAPL')
data = response.json()

if data['status'] == 'success':
    prediction = data['data']['prediction']
    print(f"方向: {prediction['direction']}")
    print(f"置信度: {prediction['confidence']:.2%}")
```

## 🐛 故障排查

### 问题1: 端口5000已被占用

**解决方案**:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### 问题2: 无法导入模块

**解决方案**:
```bash
# 重新安装依赖
pip install -r requirements.txt

# 确认在正确的环境
conda activate ic_sfp_gpu
```

### 问题3: 模型未找到

**解决方案**:
```bash
# 训练新模型
python app_integrated.py --train

# 或检查checkpoints目录
ls checkpoints/
```

### 问题4: 数据获取失败

**可能原因**:
- 网络连接问题
- API限流
- 股票代码错误

**解决方案**:
- 检查网络连接
- 使用其他数据源（配置realtime_config.yml）
- 确认股票代码正确

### 问题5: WebSocket连接失败

**解决方案**:
```bash
# 确保安装了socketio依赖
pip install flask-socketio python-socketio

# 检查防火墙设置
# 尝试使用polling传输方式（浏览器会自动降级）
```

## 📖 相关文档

- [实时数据模块文档](docs/REALTIME_DATA_MODULE.md)
- [实时预测指南](docs/REALTIME_PREDICTION_GUIDE.md)
- [可视化指南](docs/VISUALIZATION_GUIDE.md)
- [API文档](docs/API_GUIDE.md)

## 💡 最佳实践

### 1. 性能优化
- 使用缓存减少API调用
- 限制WebSocket订阅数量（建议<10只股票）
- 定期清理缓存

### 2. 生产部署
- 使用Gunicorn或uWSGI替代Flask开发服务器
- 配置Nginx反向代理
- 启用HTTPS
- 设置API限流

### 3. 数据管理
- 定期备份模型检查点
- 监控缓存大小
- 设置合理的TTL

### 4. 安全考虑
- 不要在公网暴露开发服务器
- 使用环境变量管理API密钥
- 启用CORS白名单
- 实施请求验证

## 🤝 技术支持

- 查看文档: `docs/`目录
- 运行测试: `pytest tests/`
- 查看日志: `log/`目录

## 📄 许可证

与ICSFP项目保持一致

---

**享受使用ICSFP！** 🚀
