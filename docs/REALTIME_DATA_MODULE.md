# 实时数据接入模块

## 📋 概述

实时数据接入模块为ICSFP平台提供多源实时股票数据获取、缓存和推送功能。支持多个数据源、智能缓存、WebSocket实时推送等特性。

## ✨ 主要特性

### 1. 多数据源支持
- **Yahoo Finance** (默认) - 免费，无需API密钥
- **Alpha Vantage** - 专业数据API，需要密钥
- **Tushare** - 中国A股数据，需要token

### 2. 智能缓存系统
- 内存+文件双层缓存
- 可配置的缓存过期时间
- 自动缓存失效和更新

### 3. 实时推送
- 基于WebSocket的实时数据推送
- 支持订阅/取消订阅机制
- 房间管理，按股票分组推送

### 4. 批量操作
- 支持批量获取多只股票数据
- 并发请求优化
- 失败重试机制

### 5. 自动更新
- 可选的后台自动更新
- 定时刷新关注列表
- 可配置更新间隔

## 📦 安装依赖

```bash
# 安装必需的库
pip install yfinance>=0.2.28
pip install flask-socketio>=5.3.0
pip install python-socketio>=5.9.0

# 可选：Alpha Vantage支持
pip install alpha-vantage>=2.3.1

# 可选：Tushare支持（中国A股）
pip install tushare>=1.2.89
```

或使用requirements.txt:
```bash
pip install -r requirements.txt
```

## 🔧 配置

### 1. 配置文件

编辑 `config/realtime_config.yml`:

```yaml
# 缓存设置
cache:
  dir: "cache/realtime"
  ttl: 60  # 缓存过期时间（秒）
  max_size: 1000

# 自动更新
auto_update:
  enabled: false
  interval: 300  # 5分钟

# 数据源配置
data_sources:
  yahoo_finance:
    enabled: true
    priority: 1
  
  alpha_vantage:
    enabled: false
    api_key: "YOUR_API_KEY"  # 从 https://www.alphavantage.co 获取
    priority: 2
  
  tushare:
    enabled: false
    token: "YOUR_TOKEN"  # 从 https://tushare.pro 获取
    priority: 3

# 关注列表
watch_list:
  - AAPL
  - GOOG
  - MSFT
  - AMZN
  - TSLA

# WebSocket设置
websocket:
  enabled: true
  namespace: "/realtime"
  max_connections: 100
```

### 2. API密钥获取

#### Alpha Vantage
1. 访问 https://www.alphavantage.co/support/#api-key
2. 注册账号获取免费API密钥
3. 免费版限制：5次请求/分钟，500次/天

#### Tushare
1. 访问 https://tushare.pro
2. 注册账号获取token
3. 根据积分等级有不同的访问权限

## 🚀 使用方法

### 方法1: Python脚本

```python
from api.realtime_data import get_realtime_manager

# 初始化管理器
config = {
    'cache_dir': 'cache/realtime',
    'cache_ttl': 60,
    'data_sources': {
        'yahoo_finance': {'enabled': True}
    }
}
manager = get_realtime_manager(config)

# 获取单只股票报价
quote = manager.get_realtime_quote('AAPL')
print(f"AAPL价格: ${quote['price']:.2f}")

# 批量获取多只股票
quotes = manager.get_multiple_quotes(['AAPL', 'GOOG', 'MSFT'])

# 获取历史数据
df = manager.get_historical_data('AAPL', '2025-10-01', '2025-11-04')

# 获取市场摘要
summary = manager.get_market_summary()
```

### 方法2: HTTP REST API

启动服务器:
```bash
cd D:\ICSFP\HCSF
python api/app.py
```

API端点:

#### 1. 获取单只股票报价
```http
GET /api/v1/realtime/quote/AAPL
```

响应:
```json
{
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "price": 150.25,
    "open": 149.50,
    "high": 151.00,
    "low": 149.00,
    "volume": 75000000,
    "change": 0.45,
    "change_percent": 0.30,
    "timestamp": "2025-11-04T10:30:00"
  }
}
```

#### 2. 批量获取报价
```http
POST /api/v1/realtime/quotes
Content-Type: application/json

{
  "symbols": ["AAPL", "GOOG", "MSFT"],
  "use_cache": true
}
```

#### 3. 获取历史数据
```http
GET /api/v1/realtime/historical/AAPL?start_date=2025-10-01&end_date=2025-11-04
```

#### 4. 获取市场摘要
```http
GET /api/v1/realtime/market/summary
```

#### 5. 清除缓存
```http
POST /api/v1/realtime/cache/clear
Content-Type: application/json

{
  "symbol": "AAPL"  // 可选，不填则清除所有
}
```

### 方法3: WebSocket实时推送

#### 前端连接

```javascript
// 连接WebSocket
const socket = io('/realtime');

// 监听连接
socket.on('connect', () => {
    console.log('Connected');
    
    // 订阅股票
    socket.emit('subscribe', {
        symbols: ['AAPL', 'GOOG', 'MSFT']
    });
});

// 接收市场更新
socket.on('market_update', (data) => {
    console.log('Update:', data);
    // data.type: 'initial' 或 'update'
    // data.symbol: 股票代码
    // data.data: 报价数据
});

// 取消订阅
socket.emit('unsubscribe', {
    symbols: ['AAPL']
});
```

#### Web页面

访问实时监控页面:
```
http://localhost:5000/realtime
```

## 📊 示例程序

### 运行示例

```bash
cd D:\ICSFP\HCSF
python examples/realtime_data_example.py
```

示例包括:
1. 获取单只股票实时报价
2. 批量获取多只股票报价
3. 获取历史数据
4. 获取市场摘要
5. 缓存使用演示
6. 自动更新功能

### 示例输出

```
AAPL 实时报价:
  当前价格: $150.25
  开盘价: $149.50
  最高价: $151.00
  最低价: $149.00
  成交量: 75,000,000
  涨跌额: $0.45
  涨跌幅: 0.30%
  数据来源: yahoo_finance
  更新时间: 2025-11-04T10:30:00
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      前端/客户端                          │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │   浏览器     │  │  Python脚本  │  │  移动应用     │   │
│  └─────────────┘  └─────────────┘  └──────────────┘   │
└─────────┬───────────────┬──────────────┬──────────────┘
          │               │              │
          │ HTTP/WS       │ Python       │ HTTP
          ▼               ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                    API 服务层                            │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ REST API Routes  │      │ WebSocket Server │        │
│  └──────────────────┘      └──────────────────┘        │
└─────────┬───────────────────────┬──────────────────────┘
          │                       │
          ▼                       ▼
┌─────────────────────────────────────────────────────────┐
│              实时数据管理器 (RealtimeDataManager)         │
│  ┌───────────────────┐    ┌────────────────────┐       │
│  │   数据缓存系统     │    │   自动更新调度器    │       │
│  │ (DataCache)       │    │ (Auto Update)      │       │
│  └───────────────────┘    └────────────────────┘       │
└─────────┬───────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│                   数据源层 (DataSource)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Yahoo Finance │  │Alpha Vantage │  │   Tushare    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🔍 核心组件

### 1. DataSource (抽象基类)
```python
class DataSource(ABC):
    @abstractmethod
    def get_realtime_price(self, symbol: str) -> Dict
    
    @abstractmethod
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame
    
    @abstractmethod
    def get_multiple_quotes(self, symbols: List[str]) -> Dict
```

### 2. DataCache (缓存管理器)
- 内存缓存（快速访问）
- 文件缓存（持久化）
- TTL过期机制
- 键值对存储

### 3. RealtimeDataManager (数据管理器)
- 多数据源管理
- 缓存协调
- 自动更新调度
- 数据聚合

### 4. WebSocket Server
- 连接管理
- 房间订阅
- 实时推送
- 错误处理

## 📈 性能优化

### 1. 缓存策略
- **内存优先**: 最快的访问速度
- **文件备份**: 进程重启后恢复
- **智能过期**: 根据市场状态调整TTL

### 2. 并发处理
```python
# 批量请求使用线程池
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(fetch, symbol) for symbol in symbols]
    results = [future.result() for future in futures]
```

### 3. 限流保护
```python
# API限流装饰器
@rate_limit(max_calls=5, period=60)
def get_data(symbol):
    ...
```

## 🛡️ 错误处理

### 1. 数据源失败
```python
try:
    data = primary_source.get_data(symbol)
except Exception:
    # 自动切换到备用数据源
    data = fallback_source.get_data(symbol)
```

### 2. 网络超时
```python
@retry(max_attempts=3, backoff=2)
def fetch_with_retry(symbol):
    ...
```

### 3. 数据验证
```python
def validate_quote(quote):
    if quote['price'] <= 0:
        raise ValueError("Invalid price")
    if abs(quote['change_percent']) > 50:
        raise ValueError("Abnormal price change")
```

## 📝 最佳实践

### 1. 使用缓存
```python
# ✅ 推荐：使用缓存
quote = manager.get_realtime_quote('AAPL', use_cache=True)

# ❌ 不推荐：频繁请求无缓存
for i in range(100):
    quote = manager.get_realtime_quote('AAPL', use_cache=False)
```

### 2. 批量请求
```python
# ✅ 推荐：批量请求
quotes = manager.get_multiple_quotes(['AAPL', 'GOOG', 'MSFT'])

# ❌ 不推荐：循环单独请求
for symbol in ['AAPL', 'GOOG', 'MSFT']:
    quote = manager.get_realtime_quote(symbol)
```

### 3. 资源释放
```python
# 使用完毕后停止自动更新
manager.stop_auto_update()

# 清理缓存
manager.cache.clear()
```

## 🐛 故障排查

### 问题1: 数据获取失败
```
错误: No module named 'yfinance'
解决: pip install yfinance
```

### 问题2: API限流
```
错误: Rate limit exceeded
解决: 
1. 增加缓存TTL
2. 使用批量请求
3. 启用多数据源
```

### 问题3: WebSocket断连
```
解决:
1. 检查网络连接
2. 增加心跳间隔
3. 实现自动重连
```

## 📚 API参考

完整API文档请参考:
- [REST API文档](../docs/API_GUIDE.md)
- [WebSocket协议](../docs/WEBSOCKET_PROTOCOL.md)
- [数据源文档](../docs/DATA_SOURCES.md)

## 🔄 更新日志

### v1.0.0 (2025-11-04)
- ✨ 初始版本发布
- 🎉 支持Yahoo Finance数据源
- 🚀 实现智能缓存系统
- 📡 WebSocket实时推送
- 📊 批量数据获取
- ⚡ 自动更新功能

## 🤝 贡献

欢迎提交Issue和Pull Request!

## 📄 许可证

MIT License

## 📧 联系方式

如有问题，请联系开发团队。
