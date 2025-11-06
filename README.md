# ICSFP - Intelligent Causal Stock Forecasting Platform

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**ICSFP** 是一个基于因果推理和深度学习的智能股票预测平台，集成了实时数据获取、模型训练、预测分析和可视化展示等完整功能。

---

## ✨ 最新功能 (v2.0)

### 🌐 Web可视化界面
- **高级可视化页面**: 多图表展示（价格、成交量、波动率）
- **实时数据监控**: WebSocket实时推送
- **多天预测**: 支持1-7天的预测展示
- **响应式设计**: 完美适配PC和移动端

### 🔌 实时数据模块
- **多数据源支持**: Yahoo Finance、Alpha Vantage、Tushare
- **智能缓存**: 双层缓存机制（内存+文件）
- **实时报价**: 毫秒级数据更新
- **批量获取**: 支持多只股票同时查询

### 🎯 实时预测系统
- **单只/批量预测**: 灵活的预测接口
- **多天预测**: 未来1-7天趋势预测
- **因果增强**: 可选的因果图增强预测
- **置信度评估**: 提供预测置信度和概率分布

---

## 🎯 核心特性

### 模型能力
- 🧠 **深度学习模型**: 基于GRU/LSTM的时序预测
- 🔗 **因果图增强**: 利用股票间因果关系提升预测
- 📊 **多特征融合**: 整合价格、成交量、文本等多源数据
- 🎲 **VAE架构**: 变分自编码器建模不确定性

### 数据处理
- 📈 **实时数据获取**: 支持多个数据源
- 🗂️ **智能缓存**: 优化数据访问性能
- 🔄 **自动更新**: 定时刷新市场数据
- 📝 **历史数据**: 完整的历史数据查询

### API服务
- 🌐 **RESTful API**: 标准的HTTP接口
- 🔌 **WebSocket**: 实时双向通信
- 📡 **批量处理**: 支持批量预测请求
- 📊 **数据导出**: JSON格式数据输出

### 可视化
- 📊 **多图表展示**: Chart.js专业图表
- 🎨 **精美界面**: 现代化UI设计
- 📱 **响应式布局**: 适配各种设备
- ⚡ **实时更新**: 动态数据刷新

---

## 📦 安装

### 环境要求

- Python 3.8+
- CUDA 11.7+ (可选，用于GPU加速)
- 8GB+ RAM
- 10GB+ 磁盘空间

### 快速安装

```bash
# 克隆仓库
git clone https://github.com/your-username/ICSFP.git
cd ICSFP/HCSF

# 创建虚拟环境
conda create -n ic_sfp_gpu python=3.12
conda activate ic_sfp_gpu

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

---

## 🚀 快速开始

### 方法1: 一键启动（推荐）

```bash
# 激活环境
conda activate ic_sfp_gpu

# 启动Web界面
python quickstart_web.py
```

这将自动：
- ✅ 检查环境和依赖
- ✅ 启动Web服务器（端口5000）
- ✅ 在浏览器中打开可视化页面

### 方法2: 使用集成应用

```bash
# 交互模式（菜单式操作）
python app_integrated.py --interactive

# 或直接启动Web界面
python app_integrated.py --web --browser
```

### 方法3: 直接启动API服务器

```bash
python api/app.py
```

然后访问: http://127.0.0.1:5000/static/advanced_visualization.html

---

## 📊 可用页面

启动服务器后，可以访问以下页面：

### 1. 高级可视化 (推荐)
**URL**: http://127.0.0.1:5000/static/advanced_visualization.html

**功能**:
- 📈 价格/成交量/波动率多图表
- 🎯 多天预测可视化
- 🔌 WebSocket实时推送
- 📋 历史数据表格

### 2. 基础可视化
**URL**: http://127.0.0.1:5000/static/visualization.html

**功能**:
- 📊 价格走势图
- 🎯 单只股票预测
- 💯 置信度可视化

### 3. 实时监控
**URL**: http://127.0.0.1:5000/static/realtime.html

**功能**:
- 🔌 多股票实时订阅
- ⚡ 实时报价更新
- 📊 市场统计

---

## 🎮 使用示例

### 1. Web界面操作

```
1. 在页面中输入股票代码（如: AAPL）
2. 选择时间范围（7天/30天/90天）
3. 点击"刷新全部"加载数据
4. 点击"多天预测"查看预测结果
5. 点击"连接WebSocket"启用实时推送
```

### 2. API调用

#### 获取实时报价
```bash
curl http://127.0.0.1:5000/api/v1/realtime/quote/AAPL
```

#### 实时预测
```bash
curl "http://127.0.0.1:5000/api/v1/realtime/predict/AAPL?use_causal=true"
```

#### 多天预测
```bash
curl "http://127.0.0.1:5000/api/v1/realtime/predict/horizon/AAPL?horizon_days=5"
```

### 3. Python集成

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

### 4. 命令行工具

```bash
# 实时预测单只股票
python app_integrated.py --realtime AAPL

# 批量预测多只股票
python app_integrated.py --realtime AAPL,GOOG,MSFT

# 查看预测结果
python app_integrated.py --predict AAPL
```

---

## 🏗️ 项目结构

```
HCSF/
├── api/                          # API模块
│   ├── app.py                    # Flask应用主入口
│   ├── routes.py                 # API路由
│   ├── realtime_data.py          # 实时数据模块
│   ├── realtime_predictor.py     # 实时预测器
│   └── realtime_routes.py        # 实时数据路由
├── static/                       # 静态文件
│   ├── visualization.html        # 基础可视化页面
│   ├── advanced_visualization.html  # 高级可视化页面
│   └── realtime.html             # 实时监控页面
├── config/                       # 配置文件
│   ├── config.yml                # 主配置
│   └── realtime_config.yml       # 实时数据配置
├── docs/                         # 文档
│   ├── INTEGRATION_GUIDE.md      # 集成指南
│   ├── VISUALIZATION_GUIDE.md    # 可视化指南
│   ├── REALTIME_DATA_MODULE.md   # 实时数据模块文档
│   └── REALTIME_PREDICTION_GUIDE.md  # 实时预测指南
├── Model.py                      # 模型定义
├── DataPipe.py                   # 数据管道
├── Executor.py                   # 训练执行器
├── Main.py                       # 训练主程序
├── app_integrated.py             # 集成应用入口
├── quickstart_web.py             # 快速启动脚本
└── requirements.txt              # 依赖列表
```

---

## 📖 文档

- [集成应用使用指南](INTEGRATION_GUIDE.md) - **从这里开始**
- [可视化功能指南](docs/VISUALIZATION_GUIDE.md)
- [实时数据模块文档](docs/REALTIME_DATA_MODULE.md)
- [实时预测功能指南](docs/REALTIME_PREDICTION_GUIDE.md)
- [API文档](docs/API_GUIDE.md)

---

## 🔧 配置

### 实时数据配置 (config/realtime_config.yml)

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

websocket:
  max_clients: 100
  update_interval: 5      # 推送间隔（秒）
```

### 模型配置 (config.yml)

```yaml
model:
  cell_type: gru          # RNN单元类型
  dropout: 0.3            # Dropout率
  batch_size: 32          # 批次大小
  learning_rate: 0.001    # 学习率

causal:
  use_causal: true        # 是否使用因果图
  causal_z_size: 32       # 因果隐变量维度
```

---

## 🎯 主要功能模块

### 1. 实时数据模块

**功能**:
- 多数据源支持（Yahoo Finance、Alpha Vantage、Tushare）
- 智能缓存系统（内存+文件双层）
- 实时报价和历史数据查询
- 批量获取和WebSocket推送

**示例**:
```python
from api.realtime_data import RealtimeDataManager

manager = RealtimeDataManager()
quote = manager.get_quote('AAPL')
print(f"价格: ${quote['price']}")
```

### 2. 实时预测模块

**功能**:
- 单只/批量股票预测
- 多天预测（1-7天）
- 因果图增强预测
- 置信度评估

**示例**:
```python
from api.realtime_predictor import RealtimePredictor

predictor = RealtimePredictor()
result = predictor.predict_realtime('AAPL', use_causal=True)
print(f"方向: {result['prediction']['direction']}")
print(f"置信度: {result['prediction']['confidence']:.2%}")
```

### 3. 可视化模块

**功能**:
- Chart.js专业图表
- 多图表联动展示
- WebSocket实时更新
- 响应式设计

**页面**:
- 基础可视化: 单图表+预测
- 高级可视化: 多图表+多天预测
- 实时监控: WebSocket订阅

### 4. API服务

**端点**:
- `GET /api/v1/health` - 健康检查
- `GET /api/v1/realtime/quote/<symbol>` - 实时报价
- `GET /api/v1/realtime/predict/<symbol>` - 实时预测
- `GET /api/v1/realtime/predict/horizon/<symbol>` - 多天预测

---

## 🐛 故障排查

### 端口占用
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### 依赖问题
```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 模型未找到
```bash
# 训练新模型
python app_integrated.py --train
```

### WebSocket连接失败
```bash
# 确保安装了socketio
pip install flask-socketio python-socketio
```

更多问题请参考 [集成指南](INTEGRATION_GUIDE.md#故障排查)

---

## 📈 性能指标

### 预测性能
- **准确率**: 52-60% (市场随机50%)
- **MCC**: 0.05-0.15
- **预测时间**: <100ms/股票

### 系统性能
- **API响应**: <200ms
- **WebSocket延迟**: <50ms
- **缓存命中率**: >80%
- **并发支持**: 100+客户端

---

## 🔮 未来计划

- [ ] 更多数据源支持
- [ ] 增强的因果发现算法
- [ ] 自动化交易信号
- [ ] 移动端App
- [ ] 实时告警通知
- [ ] 用户账户系统
- [ ] 数据持久化存储
- [ ] 更多技术指标

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 👥 团队

ICSFP由AI研究团队开发和维护。

---

## 📞 联系方式

- 问题反馈: [GitHub Issues](https://github.com/your-username/ICSFP/issues)
- 邮箱: your-email@example.com

---

## 🙏 致谢

感谢以下开源项目：
- PyTorch
- Flask & Flask-SocketIO
- Chart.js
- yfinance
- 以及所有贡献者

---

**享受使用ICSFP！** 🚀📈

如有问题，请查看 [集成指南](INTEGRATION_GUIDE.md) 或提交 Issue。
