# ICSFP 快速参考卡片

## 🚀 一键启动

```bash
conda activate ic_sfp_gpu
python quickstart_web.py
```

## 🌐 访问页面

| 页面 | URL | 功能 |
|------|-----|------|
| 高级可视化 | http://127.0.0.1:5000/static/advanced_visualization.html | 多图表+多天预测 |
| 基础可视化 | http://127.0.0.1:5000/static/visualization.html | 单图表+简单预测 |
| 实时监控 | http://127.0.0.1:5000/static/realtime.html | 多股票实时监控 |

## 📡 API速查

### 实时报价
```bash
curl http://127.0.0.1:5000/api/v1/realtime/quote/AAPL
```

### 历史数据
```bash
curl "http://127.0.0.1:5000/api/v1/realtime/historical/AAPL?start_date=2024-01-01&end_date=2024-12-31"
```

### 实时预测
```bash
curl "http://127.0.0.1:5000/api/v1/realtime/predict/AAPL?use_causal=true"
```

### 多天预测
```bash
curl "http://127.0.0.1:5000/api/v1/realtime/predict/horizon/AAPL?horizon_days=5"
```

## 🎮 命令行工具

```bash
# Web界面（自动打开浏览器）
python app_integrated.py --web --browser

# 交互模式
python app_integrated.py --interactive

# 实时预测
python app_integrated.py --realtime AAPL,GOOG,MSFT

# 训练模型
python app_integrated.py --train
```

## 🔧 常用配置

### 实时数据配置
文件: `config/realtime_config.yml`

```yaml
cache:
  memory_ttl: 60      # 内存缓存(秒)
  file_ttl: 3600      # 文件缓存(秒)

data_sources:
  default: yahoo_finance
```

### 模型配置
文件: `config.yml`

```yaml
model:
  batch_size: 32
  learning_rate: 0.001
  dropout: 0.3
```

## 🐛 快速排错

### 端口占用
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### 重装依赖
```bash
pip install -r requirements.txt --force-reinstall
```

### 训练新模型
```bash
python app_integrated.py --train
```

## 📊 页面使用

### 高级可视化页面
1. 输入股票代码（如 AAPL）
2. 选择时间范围（7/30/90天）
3. 点击"🔄 刷新全部"
4. 点击"🎯 多天预测"
5. 点击"🔌 连接WebSocket"

### 基础可视化页面
1. 输入股票代码
2. 选择历史天数
3. 点击"🔍 加载数据"
4. 点击"🎯 预测"

### 实时监控页面
1. 点击"连接WebSocket"
2. 输入股票代码
3. 点击"订阅"
4. 查看实时更新

## 💡 Python集成

```python
import requests

# 获取报价
response = requests.get('http://127.0.0.1:5000/api/v1/realtime/quote/AAPL')
quote = response.json()['data']

# 预测
response = requests.get('http://127.0.0.1:5000/api/v1/realtime/predict/AAPL')
prediction = response.json()['data']['prediction']

print(f"价格: ${quote['price']:.2f}")
print(f"方向: {prediction['direction']}")
print(f"置信度: {prediction['confidence']:.2%}")
```

## 📚 文档快速链接

- [集成指南](INTEGRATION_GUIDE.md) - 完整使用说明
- [可视化指南](docs/VISUALIZATION_GUIDE.md) - 页面使用详解
- [实时数据模块](docs/REALTIME_DATA_MODULE.md) - 数据接入文档
- [实时预测指南](docs/REALTIME_PREDICTION_GUIDE.md) - 预测功能文档

## 📞 获取帮助

```bash
# 查看帮助
python app_integrated.py --help

# 检查环境
python quickstart_web.py

# 运行测试
python test_visualization.py
```

## 🎯 推荐工作流

### 新用户
```
quickstart_web.py → 体验Web界面 → 阅读集成指南 → 尝试API
```

### 开发者
```
阅读文档 → 测试API → Python集成 → 生产部署
```

### 交易员
```
启动监控页面 → 订阅股票 → 查看预测 → 做出决策
```

---

**版本**: v2.0  
**更新**: 2025年11月5日  
**状态**: 生产就绪 ✅
